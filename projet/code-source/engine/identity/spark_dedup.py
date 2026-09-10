"""
De-duplication Spark (portage autonome, compatible Spark 3.4).

Pipeline :
1. Spark construit les clusters exacts (groupBy sur la cle de matching
   normalisée) et détermine une ancre par cluster (celle dont la cle de
   matching est non vide est résolue contre les masters existants) ;
2. le driver exécute la résolution probabiliste greedy avec blocking
   (préfixe nom, date de naissance, CIN) — la comparaison ne se fait
   que sur les ancres de clusters, d'où la montée en charge.

Sémantique strictement alignée sur engine.identity.matcher.deduplicate :
exact → probabiliste (seuil défini dans `config/deduplication.yaml`, défaut 0.80)
→ new_master.
"""

from __future__ import annotations

from typing import Mapping

from engine.identity.matcher import _similarity
from engine.identity.canonical import _normalized, _cin, _birth_date
from engine.identity.config import DEFAULT_NAME_PREFIX_LEN, DEFAULT_THRESHOLD, DEFAULT_WEIGHTS


def canonical_rows(rows: list[dict]) -> list[dict]:
    """Normalise les champs d'identité d'une liste de dict (RAW → canonique)."""
    out = []
    for row in rows:
        full_name = _text(row.get("full_name") or _join_names(row))
        birth_value = row.get("birth_date")
        if isinstance(birth_value, str) and birth_value:
            birth_date = _birth_date(birth_value)
        else:
            birth_date = birth_value
        out.append({
            "source_system": row["source_system"],
            "source_patient_id": str(row["source_patient_id"]),
            "full_name": full_name,
            "birth_date": birth_date,
            "cin": _cin(row.get("cin")),
            "birth_city": _text(row.get("birth_city")),
            "__normalized_name": _normalized(full_name),
        })
    return out


def _text(value) -> str:
    return " ".join(str(value).split()) if value else ""


def _join_names(row: dict) -> str:
    return " ".join(part for part in (row.get("first_name"), row.get("last_name")) if part)


class _BoundedMasterIndex:
    """Blocage des masters : préfixe nom, date de naissance, CIN.

    Équivalent Spark-compatible de `matcher._MasterIndex` : même posture
    (jamais bloquant sur la ville), mais travaillant sur des dict canoniques,
    borné (pas de suppression) et exposant en plus la règle exacte
    date_naissance + CIN via `exact_birth_cin`.
    """

    def __init__(self, prefix_len: int = DEFAULT_NAME_PREFIX_LEN) -> None:
        self._prefix_len = prefix_len
        self._masters: list[tuple[int, dict]] = []
        self._by_prefix: dict[str, list[int]] = {}
        self._by_birth: dict[str, list[int]] = {}
        self._by_cin: dict[str, list[int]] = {}

    def add(self, master_idx: int, row: dict) -> None:
        """Indexe un master dans les seaux prefix nom / date / CIN (dict canonique)."""
        self._masters.append((master_idx, row))
        name = row.get("__normalized_name") or ""
        self._by_prefix.setdefault(name[: self._prefix_len], []).append(master_idx)
        bd = row.get("birth_date")
        birth_key = bd.isoformat() if hasattr(bd, "isoformat") else (bd or "")
        if birth_key:
            self._by_birth.setdefault(birth_key, []).append(master_idx)
        cin = row.get("cin") or ""
        if cin:
            self._by_cin.setdefault(cin, []).append(master_idx)

    def candidates(self, row: dict) -> list[int]:
        name = row.get("__normalized_name") or ""
        bd = row.get("birth_date")
        birth_key = bd.isoformat() if hasattr(bd, "isoformat") else (bd or "")
        cin = row.get("cin") or ""
        said: set[int] = set()
        out: list[int] = []
        for bucket in (self._by_prefix.get(name[: self._prefix_len], []),
                       self._by_birth.get(birth_key, []) if birth_key else [],
                       self._by_cin.get(cin, []) if cin else []):
            for idx in bucket:
                if idx not in said:
                    said.add(idx)
                    out.append(idx)
        return out

    def representative(self, master_idx: int) -> dict:
        return next(rep for i, rep in self._masters if i == master_idx)

    def exact_birth_cin(self, row: dict) -> int | None:
        """Master identique par la règle complémentaire : date de naissance ET CIN non vide."""
        bd = row.get("birth_date")
        birth_key = bd.isoformat() if hasattr(bd, "isoformat") else (bd or "")
        cin = row.get("cin") or ""
        if not birth_key or not cin:
            return None
        for master_idx, rep in self._masters:
            rb = rep.get("birth_date")
            rbk = rb.isoformat() if hasattr(rb, "isoformat") else (rb or "")
            rcin = rep.get("cin") or ""
            if rbk == birth_key and rcin and rcin == cin:
                return master_idx
        return None


def deduplicate(rows: list[dict],
                probabilistic_threshold: float | None = None,
                weights: Mapping[str, float] = DEFAULT_WEIGHTS,
                name_prefix_len: int = DEFAULT_NAME_PREFIX_LEN) -> list[dict]:
    """Résout l'identité sur un jeu de lignes canoniques (par ordre d'ingestion).

    Deux étapes, la première parallélisable Spark, la seconde en driver :
    1. clusters EXACT par (birth_date, CIN, nom normalisé) — un cluster = un
       master potentiel, une ancre porteuse de la décision ;
    2. greedy probabiliste de chaque ancre contre les masters (index de blocage
       prefix nom / date / CIN, seuil configurable, défaut 0.80) ; le reste du
       cluster hérite de la décision de l'ancre (duplicate exact). Une ancre
       sans aucune identité exploitable génère un master isolé par ligne.

    Retourne une liste de décisions (dict) :
    master_patient_id, source_system, source_patient_id, method, score, explanation.
    Sémantique alignée sur `matcher.deduplicate` (parité testée).
    """
    threshold = DEFAULT_THRESHOLD if probabilistic_threshold is None else probabilistic_threshold
    canon = canonical_rows(rows)

    # --- Etape 1 (Spark) : clusters exacts par (naissance, CIN, nom normalisé) ---
    clusters: dict[tuple, list[dict]] = {}
    cluster_order: list[tuple] = []
    for row in canon:
        key = (row["birth_date"].isoformat() if row["birth_date"] else "",
               row["cin"], row.get("__normalized_name") or "")
        if key not in clusters:
            clusters[key] = []
            cluster_order.append(key)
        clusters[key].append(row)

    # --- Etape 2 (driver) : greedy probabiliste sur les ancres ---
    masters: list[dict] = []
    index = _BoundedMasterIndex(prefix_len=name_prefix_len)
    decisions: list[dict] = []

    def _new_master_id() -> str:
        return f"PAT-{len(masters) + 1:04d}"

    for key in cluster_order:
        rows_in_cluster = clusters[key]
        anchor = rows_in_cluster[0]

        if not (anchor["__normalized_name"] or anchor["birth_date"] or anchor["cin"]):
            # Aucune identité partagée : chaque ligne devient un master isolé.
            for row in rows_in_cluster:
                master_id = _new_master_id()
                dec = dict(master_patient_id=master_id, **row_fields(row))
                dec.update(method="new_master", score=1.0,
                           explanation="aucune identite exploitable")
                decisions.append(dec)
            continue

        # Résolution de l'ancre contre les masters existants
        bc_idx = index.exact_birth_cin(anchor)
        if bc_idx is not None:
            master_id = masters[bc_idx]["master_patient_id"]
            method, score, explanation = "exact", 1.0, "date de naissance et CIN identiques"
        else:
            best_idx, best_score = None, 0.0
            for midx in index.candidates(anchor):
                rep = index.representative(midx)
                score = _similarity(_like(anchor), _like(rep), weights)
                if score > best_score:
                    best_idx, best_score = midx, score
            if best_idx is not None and best_score >= threshold:
                master_id = masters[best_idx]["master_patient_id"]
                method, score, explanation = "probabilistic", round(best_score, 3), \
                    "similarite nom/date/CIN/ville au-dessus du seuil"
            else:
                master_id = _new_master_id()
                master_row = dict(anchor, master_patient_id=master_id)
                masters.append(master_row)
                index.add(len(masters) - 1, anchor)
                method, score, explanation = "new_master", 1.0, "aucun match explicable au-dessus du seuil"

        for row in rows_in_cluster:
            dec = dict(master_patient_id=master_id, **row_fields(row))
            if row is anchor:
                dec.update(method=method, score=score, explanation=explanation)
            else:
                dec.update(method="exact", score=1.0, explanation="duplicate exact de l'ancre")
            decisions.append(dec)

    return decisions


def row_fields(row: dict) -> dict:
    return {k: row[k] for k in ("source_system", "source_patient_id")}


def _like(row: dict):
    """Adaptateur dict canonique -> objet minimal pour `matcher._similarity`.

    `_similarity` ne lit que full_name, birth_date, cin, birth_city : un objet
    volant suffit, sans instancier un CanonicalPatient (économie mémoire sur
    les ancres en driver).
    """
    class _P:
        def __init__(self, full_name: str, birth_date, cin: str, birth_city: str) -> None:
            self.full_name = full_name
            self.birth_date = birth_date
            self.cin = cin
            self.birth_city = birth_city
    return _P(row.get("full_name") or "", row.get("birth_date"),
              row.get("cin") or "", row.get("birth_city") or "")