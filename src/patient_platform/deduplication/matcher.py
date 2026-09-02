from dataclasses import dataclass

from rapidfuzz import fuzz

from patient_platform.transform.canonical import CanonicalPatient, matching_key


@dataclass(frozen=True)
class MatchDecision:
    master_patient_id: str
    source_system: str
    source_patient_id: str
    method: str
    score: float
    explanation: str


def _similarity(left: CanonicalPatient, right: CanonicalPatient) -> float:
    name_score = fuzz.ratio(
        left.full_name.lower(), right.full_name.lower()) / 100.0
    birth_score = float(
        left.birth_date is not None and left.birth_date == right.birth_date)
    phone_score = float(bool(left.phone) and left.phone == right.phone)
    return round((name_score * 0.5) + (birth_score * 0.3) + (phone_score * 0.2), 3)


def deduplicate(patients: list[CanonicalPatient], probabilistic_threshold: float = 0.80) -> list[MatchDecision]:
    masters: list[CanonicalPatient] = []
    decisions: list[MatchDecision] = []

    for patient in patients:
        exact_index = next((index for index, master in enumerate(masters)
                            if matching_key(patient) == matching_key(master)
                            or (patient.birth_date is not None
                                and patient.birth_date == master.birth_date
                                and bool(patient.phone)
                                and patient.phone == master.phone)), None)
        if exact_index is not None:
            master_id = f"PAT-{exact_index + 1:04d}"
            decisions.append(MatchDecision(master_id, patient.source_system, patient.source_patient_id,
                             "exact", 1.0, "nom, date de naissance et telephone normalises identiques"))
            continue

        candidate_index, candidate_score = None, 0.0
        for index, master in enumerate(masters):
            score = _similarity(patient, master)
            if score > candidate_score:
                candidate_index, candidate_score = index, score
        if candidate_index is not None and candidate_score >= probabilistic_threshold:
            master_id = f"PAT-{candidate_index + 1:04d}"
            decisions.append(MatchDecision(master_id, patient.source_system, patient.source_patient_id,
                             "probabilistic", candidate_score, "similarite nom/date/telephone au-dessus du seuil"))
        else:
            masters.append(patient)
            master_id = f"PAT-{len(masters):04d}"
            decisions.append(MatchDecision(master_id, patient.source_system, patient.source_patient_id,
                             "new_master", 1.0, "aucun match explicable au-dessus du seuil"))

    return decisions
