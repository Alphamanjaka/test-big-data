from datetime import date

from patient_platform.pipeline import run_pipeline


def test_pipeline_creates_explicable_identity_map_for_duplicate_patient(tmp_path):
    result = run_pipeline(
        "data/raw",
        tmp_path / "runtime.log",
        tmp_path / "LOGS.md",
    )

    assert len(result.patients) == 18
    assert len(result.business_records) == 18
    assert {record.domain for record in result.business_records} == {
        "purchase", "consultation", "imaging_exam"
    }
    assert len(
        {decision.master_patient_id for decision in result.identity_map}) == 11

    imaging_jean = next(decision for decision in result.identity_map if decision.source_system ==
                        "imaging" and decision.source_patient_id == "IMG001")
    assert imaging_jean.master_patient_id == "PAT-0001"
    assert imaging_jean.method == "exact"
    assert imaging_jean.score == 1.0
    assert "normalises" in imaging_jean.explanation


def test_pipeline_triggers_probabilistic_match_on_phone_typo(tmp_path):
    result = run_pipeline(
        "data/raw",
        tmp_path / "runtime.log",
        tmp_path / "LOGS.md",
    )

    decision = next(decision for decision in result.identity_map if decision.source_system ==
                    "consultation" and decision.source_patient_id == "53")
    assert decision.master_patient_id == "PAT-0004"
    assert decision.method == "probabilistic"
    assert decision.score == 0.8

    methods = {decision.method for decision in result.identity_map}
    assert {"exact", "probabilistic", "new_master"} <= methods


def test_canonical_date_and_phone_are_standardized(tmp_path):
    result = run_pipeline(
        "data/raw",
        tmp_path / "runtime.log",
        tmp_path / "LOGS.md",
    )
    jean = result.patients[0]

    assert jean.birth_date == date(1990, 1, 10)
    assert jean.phone == "0341234567"
