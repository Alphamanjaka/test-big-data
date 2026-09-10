"""Modèle canonique patient et normalisation (portage autonome)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import re
import unicodedata

import pandas as pd


@dataclass(frozen=True)
class CanonicalPatient:
    source_system: str
    source_patient_id: str
    first_name: str
    last_name: str
    full_name: str
    birth_date: date | None
    cin: str
    birth_city: str
    address: str
    gender: str
    source_file: str


def _is_missing(value) -> bool:
    try:
        return value is None or bool(pd.isna(value))
    except (TypeError, ValueError):
        return False


def _text(value) -> str:
    if _is_missing(value):
        return ""
    return " ".join(str(value).strip().split())


def _normalized(value: str) -> str:
    if value is None:
        return ""
    without_accents = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", without_accents.lower())


def _cin(value) -> str:
    """Normalise un CIN en ne gardant que les chiffres (ex: 101 02404 5 -> 101024045)."""
    if value is None:
        return ""
    digits = re.sub(r"\D", "", str(value))
    return digits if 6 <= len(digits) <= 12 else ""


def _gender(value) -> str:
    text = _text(value).upper()
    if text in {"M", "H", "HOMME", "MALE", "MASCULIN"}:
        return "M"
    if text in {"F", "FEMME", "FEMALE", "FEMININ"}:
        return "F"
    return ""


def _birth_date(value) -> date | None:
    value = value.strip() if value is not None else ""
    fmt = "%Y-%m-%d" if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value) else None
    if fmt is None and re.fullmatch(r"\d{4}/\d{2}/\d{2}", value):
        fmt = "%Y/%m/%d"
    parsed = pd.to_datetime(value, format=fmt, dayfirst=fmt is None, errors="coerce")
    return None if pd.isna(parsed) else parsed.date()


def matching_key(patient: CanonicalPatient) -> tuple[str, str, str]:
    """Clé composite de matching exact : (birth_date, cin, nom normalisé).

    Ordre volontaire : la date de naissance et le CIN sont des identifiants
    plus discriminants que le nom ; les deux variantes d'écriture d'un même
    nom (inversion prénom/nom) aboutissent à la même clé après normalisation.
    Utilisée par le matching exact de `matcher` et par le clustering Spark de
    `spark_dedup` — les deux implémentations doivent rester strictement à
    l'identique (parité testée dans `tests/test_matcher.py`).
    """
    birth_date = patient.birth_date.isoformat() if patient.birth_date else ""
    return (birth_date, patient.cin, _normalized(patient.full_name))


def map_patient(row, source_system: str, source_file: str = "") -> CanonicalPatient:
    """Convertit une ligne brute d'une source en `CanonicalPatient`.

    Chaque source utilise ses propres conventions de colonnes :
    - ``pharmacy`` : nom_complet découpé en prénom/nom, clé client_id, CIN,
      naissance, sexe, adresse ;
    - ``consultation`` : prenom/nom séparés, clé patient_code, no_cin,
      date_naiss, genre (pas d'adresse) ;
    - ``imaging`` : patient_name (avec points supprimés), id_personne,
      cin_number, dob, birth_place (pas d'adresse).

    Les valeurs passent systématiquement par les normalisations partagées
    (_text, _cin, _gender, _birth_date) afin d'obtenir un référentiel commun
    des le RAW, indispensable a un matching exact/probabiliste fiable ensuite.
    """
    if source_system == "pharmacy":
        name_parts = _text(row["nom_complet"]).split(" ", 1)
        first_name, last_name = (name_parts + [""])[:2]
        full_name = _text(row["nom_complet"])
        source_id = _text(row["client_id"])
        cin = _cin(row.get("cin", ""))
        birth_city = _text(row.get("ville_naissance", ""))
        address = _text(row["adresse"])
        birth_value = _text(row["naissance"])
        gender_value = row.get("sexe", "")
    elif source_system == "consultation":
        first_name = _text(row["prenom"])
        last_name = _text(row["nom"])
        full_name = f"{first_name} {last_name}".strip()
        source_id = _text(row["patient_code"])
        cin = _cin(row.get("no_cin", ""))
        birth_city = _text(row.get("ville_nai", ""))
        address = ""
        birth_value = _text(row["date_naiss"])
        gender_value = row.get("genre", "")
    elif source_system == "imaging":
        full_name = _text(row["patient_name"]).replace(".", "")
        name_parts = full_name.split(" ", 1)
        first_name, last_name = (name_parts + [""])[:2]
        source_id = _text(row["id_personne"])
        cin = _cin(row.get("cin_number", ""))
        birth_city = _text(row.get("birth_place", ""))
        address = ""
        birth_value = _text(row["dob"])
        gender_value = row.get("sex", "")
    else:
        raise ValueError(f"Unsupported source system: {source_system}")

    return CanonicalPatient(
        source_system=source_system,
        source_patient_id=source_id,
        first_name=first_name,
        last_name=last_name,
        full_name=full_name,
        birth_date=_birth_date(birth_value),
        cin=cin,
        birth_city=birth_city,
        address=address,
        gender=_gender(gender_value),
        source_file=_text(source_file),
    )


def from_dict(row: dict) -> CanonicalPatient:
    """Construit un CanonicalPatient depuis un dict canonique (source agnostique).

    Champs attendus : source_system, source_patient_id, full_name (ou
    first_name+last_name), birth_date (date ou chaîne ISO), cin, birth_city,
    address, gender, source_file (optionnel).
    """
    full_name = _text(row.get("full_name"))
    if not full_name:
        full_name = " ".join(part for part in (row.get("first_name"), row.get("last_name")) if part)
    name_parts = full_name.split(" ", 1)
    return CanonicalPatient(
        source_system=_text(row["source_system"]),
        source_patient_id=_text(row["source_patient_id"]),
        first_name=name_parts[0],
        last_name=name_parts[1] if len(name_parts) > 1 else "",
        full_name=full_name,
        birth_date=row.get("birth_date") if isinstance(row.get("birth_date"), date) else _birth_date(row.get("birth_date") or ""),
        cin=_cin(row.get("cin")),
        birth_city=_text(row.get("birth_city")),
        address=_text(row.get("address")),
        gender=_gender(row.get("gender")),
        source_file=_text(row.get("source_file")),
    )