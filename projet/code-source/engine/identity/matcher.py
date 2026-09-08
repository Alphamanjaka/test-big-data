"""
Matching exact + probabiliste (portage autonome de test_bigdata).

Règle de resolution d'identité, sceau explicable :
- batiment 1 : matching EXACT sur (date_naissance, telephone, nom normalisé) ;
- règle exacte complémentaire : même date de naissance ET même téléphone non vide
  (absorbe les inversions prénom/nom) ;
- batiment 2 : probabiliste sur les candidats d'un index de blocage partageant
  préfixe de nom normalisé, date de naissance ou téléphone ; score pondéré
  nom 0.5 / date 0.3 / téléphone 0.2 ; seuil 0.80 ;
- sinon : nouveau master patient (new_master).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from rapidfuzz import fuzz

from engine.identity.canonical import CanonicalPatient, matching_key, _normalized


@dataclass(frozen=True)
class MatchDecision:
    master_patient_id: str
    source_system: str
    source_patient_id: str
    method: str
    score: float
    explanation: str


def _similarity(left: CanonicalPatient, right: CanonicalPatient) -> float:
    name_score = fuzz.ratio(left.full_name.lower(), right.full_name.lower()) / 100.0
    birth_score = float(left.birth_date is not None and left.birth_date == right.birth_date)
    phone_score = float(bool(left.phone) and left.phone == right.phone)
    return round((name_score * 0.5) + (birth_score * 0.3) + (phone_score * 0.2), 3)


def _name_prefix(patient: CanonicalPatient) -> str:
    return _normalized(patient.full_name)[:4]


class _MasterIndex:
    """Index de blocage : préfixe nom, date de naissance, téléphone."""

    def __init__(self) -> None:
        self._by_prefix: dict[str, list[int]] = {}
        self._by_birth: dict[str, list[int]] = {}
        self._by_phone: dict[str, list[int]] = {}

    def add(self, index: int, master: CanonicalPatient) -> None:
        self._by_prefix.setdefault(_name_prefix(master), []).append(index)
        if master.birth_date is not None:
            self._by_birth.setdefault(master.birth_date.isoformat(), []).append(index)
        if master.phone:
            self._by_phone.setdefault(master.phone, []).append(index)

    def candidates(self, patient: CanonicalPatient) -> Iterable[int]:
        said: set[int] = set()
        buckets = [self._by_prefix.get(_name_prefix(patient), [])]
        if patient.birth_date is not None:
            buckets.append(self._by_birth.get(patient.birth_date.isoformat(), []))
        if patient.phone:
            buckets.append(self._by_phone.get(patient.phone, []))
        for bucket in buckets:
            for index in bucket:
                if index not in said:
                    said.add(index)
                    yield index


def deduplicate(patients: list[CanonicalPatient], probabilistic_threshold: float = 0.80) -> list[MatchDecision]:
    masters: list[CanonicalPatient] = []
    master_index = _MasterIndex()
    decisions: list[MatchDecision] = []

    for patient in patients:
        exact_index = next((
            index for index, master in enumerate(masters)
            if matching_key(patient) == matching_key(master)
            or (patient.birth_date is not None
                and patient.birth_date == master.birth_date
                and bool(patient.phone)
                and patient.phone == master.phone)
        ), None)
        if exact_index is not None:
            master_id = f"PAT-{exact_index + 1:04d}"
            decisions.append(MatchDecision(master_id, patient.source_system, patient.source_patient_id,
                             "exact", 1.0, "nom, date de naissance et telephone normalises identiques"))
            continue

        candidate_index, candidate_score = None, 0.0
        for index in master_index.candidates(patient):
            score = _similarity(patient, masters[index])
            if score > candidate_score:
                candidate_index, candidate_score = index, score
        if candidate_index is not None and candidate_score >= probabilistic_threshold:
            master_id = f"PAT-{candidate_index + 1:04d}"
            decisions.append(MatchDecision(master_id, patient.source_system, patient.source_patient_id,
                             "probabilistic", candidate_score, "similarite nom/date/telephone au-dessus du seuil"))
        else:
            masters.append(patient)
            master_index.add(len(masters) - 1, patient)
            master_id = f"PAT-{len(masters):04d}"
            decisions.append(MatchDecision(master_id, patient.source_system, patient.source_patient_id,
                             "new_master", 1.0, "aucun match explicable au-dessus du seuil"))

    return decisions