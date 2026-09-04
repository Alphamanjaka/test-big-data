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
    phone: str
    address: str
    source_file: str


def _is_missing(value: object) -> bool:
    try:
        return value is None or bool(pd.isna(value))
    except (TypeError, ValueError):
        return False


def _text(value: object) -> str:
    if _is_missing(value):
        return ""
    return " ".join(str(value).strip().split())


def _normalized(value: str) -> str:
    if value is None:
        return ""
    without_accents = unicodedata.normalize(
        "NFKD", value).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", without_accents.lower())


def _phone(value: str) -> str:
    if value is None:
        return ""
    digits = re.sub(r"\D", "", value)
    if digits.startswith("261") and len(digits) >= 11:
        return "0" + digits[-9:]
    return digits


def _birth_date(value: str) -> date | None:
    value = value.strip() if value is not None else ""
    date_format = "%Y-%m-%d" if re.fullmatch(
        r"\d{4}-\d{2}-\d{2}", value) else None
    if date_format is None and re.fullmatch(r"\d{4}/\d{2}/\d{2}", value):
        date_format = "%Y/%m/%d"
    parsed = pd.to_datetime(value, format=date_format,
                            dayfirst=date_format is None, errors="coerce")
    return None if pd.isna(parsed) else parsed.date()


def map_patient(row: pd.Series, source_system: str) -> CanonicalPatient:
    if source_system == "pharmacy":
        name_parts = _text(row["nom_complet"]).split(" ", 1)
        first_name, last_name = (name_parts + [""])[:2]
        full_name = _text(row["nom_complet"])
        source_id = _text(row["client_id"])
        phone = _phone(_text(row["telephone"]))
        address = _text(row["adresse"])
        birth_value = _text(row["naissance"])
    elif source_system == "consultation":
        first_name = _text(row["prenom"])
        last_name = _text(row["nom"])
        full_name = f"{first_name} {last_name}".strip()
        source_id = _text(row["patient_code"])
        phone = _phone(_text(row["phone_number"]))
        address = ""
        birth_value = _text(row["date_naiss"])
    elif source_system == "imaging":
        full_name = _text(row["patient_name"]).replace(".", "")
        name_parts = full_name.split(" ", 1)
        first_name, last_name = (name_parts + [""])[:2]
        source_id = _text(row["id_personne"])
        phone = _phone(_text(row["tel"]))
        address = ""
        birth_value = _text(row["dob"])
    else:
        raise ValueError(f"Unsupported source system: {source_system}")

    return CanonicalPatient(
        source_system=source_system,
        source_patient_id=source_id,
        first_name=first_name,
        last_name=last_name,
        full_name=full_name,
        birth_date=_birth_date(birth_value),
        phone=phone,
        address=address,
        source_file=_text(row["source_file"]),
    )


def standardize_patients(frame: pd.DataFrame, source_system: str) -> list[CanonicalPatient]:
    return [map_patient(row, source_system) for _, row in frame.iterrows()]


def matching_key(patient: CanonicalPatient) -> tuple[str, str, str]:
    birth_date = patient.birth_date.isoformat() if patient.birth_date else ""
    return (birth_date, patient.phone, _normalized(patient.full_name))
