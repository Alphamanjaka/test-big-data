from datetime import date

from patient_platform.pipeline import run_pipeline


def test_pipeline_creates_explicable_identity_map_for_duplicate_patient(tmp_path):
    result = run_pipeline(
        "data/raw",
        tmp_path / "runtime.log",
        tmp_path / "LOGS.md",
    )

    assert len(result.patients) == 6
    assert len(result.business_records) == 6
    assert {record.domain for record in result.business_records} == {
        "purchase", "consultation", "imaging_exam"
    }
    assert len(
        {decision.master_patient_id for decision in result.identity_map}) == 2

    imaging_jean = next(decision for decision in result.identity_map if decision.source_system ==
                        "imaging" and decision.source_patient_id == "IMG001")
    assert imaging_jean.master_patient_id == "PAT-0001"
    assert imaging_jean.method == "exact"
    assert imaging_jean.score == 1.0
    assert "normalises" in imaging_jean.explanation


def test_canonical_date_and_phone_are_standardized(tmp_path):
    result = run_pipeline(
        "data/raw",
        tmp_path / "runtime.log",
        tmp_path / "LOGS.md",
    )
    jean = result.patients[0]

    assert jean.birth_date == date(1990, 1, 10)
    assert jean.phone == "0341234567"
