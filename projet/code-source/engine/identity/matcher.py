"""
Matching exact + probabiliste (portage autonome de test_bigdata).

Règle de resolution d'identité, sceau explicable :
- batiment 1 : matching EXACT sur (date_naissance, CIN, nom normalisé) ;
- règle exacte complémentaire : même date de naissance ET même CIN non vide
  (absorbe les inversions prénom/nom) ;
- batiment 2 : probabiliste sur les candidats d'un index de blocage partageant
  préfixe de nom normalisé, date de naissance ou CIN ; score pondéré
  (poids et seuil définis dans `config/deduplication.yaml`, défauts
  nom 0.5 / date 0.3 / CIN 0.1 / ville 0.1, seuil 0.80) ;
- sinon : nouveau master patient (new_master).

Le CIN, quand il est présent (~75 % des patients), est une clé forte : il
participe au matching exact et à la règle complémentaire. La ville de
naissance n'est jamais bloquante : elle n'apporte qu'un faible poids au score.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from rapidfuzz import fuzz

from engine.identity.canonical import CanonicalPatient, matching_key, _normalized
from engine.identity.config import DEFAULT_NAME_PREFIX_LEN, DEFAULT_THRESHOLD, DEFAULT_WEIGHTS


@dataclass(frozen=True)
class MatchDecision:
    master_patient_id: str
    source_system: str
    source_patient_id: str
    method: str
    score: float
    explanation: str


def _similarity(left: CanonicalPatient, right: CanonicalPatient,
                weights: Mapping[str, float] = DEFAULT_WEIGHTS) -> float:
    name_score = fuzz.ratio(left.full_name.lower(), right.full_name.lower()) / 100.0
    birth_score = float(left.birth_date is not None and left.birth_date == right.birth_date)
    cin_score = float(bool(left.cin) and left.cin == right.cin)
    city_score = float(
        bool(left.birth_city) and bool(right.birth_city)
        and _normalized(left.birth_city) == _normalized(right.birth_city)
    )
    return round((name_score * weights["name"])
                 + (birth_score * weights["birth_date"])
                 + (cin_score * weights["cin"])
                 + (city_score * weights["birth_city"]), 3)


def _name_prefix(patient: CanonicalPatient, prefix_len: int = DEFAULT_NAME_PREFIX_LEN) -> str:
    return _normalized(patient.full_name)[:prefix_len]


class _MasterIndex:
    """Index de blocage : préfixe nom, date de naissance, CIN."""

    def __init__(self, prefix_len: int = DEFAULT_NAME_PREFIX_LEN) -> None:
        self._prefix_len = prefix_len
        self._by_prefix: dict[str, list[int]] = {}
        self._by_birth: dict[str, list[int]] = {}
        self._by_cin: dict[str, list[int]] = {}

    def add(self, index: int, master: CanonicalPatient) -> None:
        self._by_prefix.setdefault(_name_prefix(master, self._prefix_len), []).append(index)
        if master.birth_date is not None:
            self._by_birth.setdefault(master.birth_date.isoformat(), []).append(index)
        if master.cin:
            self._by_cin.setdefault(master.cin, []).append(index)

    def candidates(self, patient: CanonicalPatient) -> Iterable[int]:
        said: set[int] = set()
        buckets = [self._by_prefix.get(_name_prefix(patient, self._prefix_len), [])]
        if patient.birth_date is not None:
            buckets.append(self._by_birth.get(patient.birth_date.isoformat(), []))
        if patient.cin:
            buckets.append(self._by_cin.get(patient.cin, []))
        for bucket in buckets:
            for index in bucket:
                if index not in said:
                    said.add(index)
                    yield index


def deduplicate(patients: list[CanonicalPatient],
                probabilistic_threshold: float | None = None,
                weights: Mapping[str, float] = DEFAULT_WEIGHTS,
                name_prefix_len: int = DEFAULT_NAME_PREFIX_LEN) -> list[MatchDecision]:
    threshold = DEFAULT_THRESHOLD if probabilistic_threshold is None else probabilistic_threshold
    masters: list[CanonicalPatient] = []
    master_index = _MasterIndex(prefix_len=name_prefix_len)
    decisions: list[MatchDecision] = []

    for patient in patients:
        exact_index = next((
            index for index, master in enumerate(masters)
            if matching_key(patient) == matching_key(master)
            or (patient.birth_date is not None
                and patient.birth_date == master.birth_date
                and bool(patient.cin)
                and patient.cin == master.cin)
        ), None)
        if exact_index is not None:
            master_id = f"PAT-{exact_index + 1:04d}"
            decisions.append(MatchDecision(master_id, patient.source_system, patient.source_patient_id,
                             "exact", 1.0, "nom, date de naissance et CIN normalises identiques"))
            continue

        candidate_index, candidate_score = None, 0.0
        for index in master_index.candidates(patient):
            score = _similarity(patient, masters[index], weights)
            if score > candidate_score:
                candidate_index, candidate_score = index, score
        if candidate_index is not None and candidate_score >= threshold:
            master_id = f"PAT-{candidate_index + 1:04d}"
            decisions.append(MatchDecision(master_id, patient.source_system, patient.source_patient_id,
                             "probabilistic", candidate_score, "similarite nom/date/CIN/ville au-dessus du seuil"))
        else:
            masters.append(patient)
            master_index.add(len(masters) - 1, patient)
            master_id = f"PAT-{len(masters):04d}"
            decisions.append(MatchDecision(master_id, patient.source_system, patient.source_patient_id,
                             "new_master", 1.0, "aucun match explicable au-dessus du seuil"))

    return decisions