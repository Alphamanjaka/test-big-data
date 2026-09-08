from patient_platform.config import load_data_root
from patient_platform.pipeline import run_pipeline


if __name__ == "__main__":
    result = run_pipeline(load_data_root())
    for decision in result.identity_map:
        print(
            f"{decision.source_system}:{decision.source_patient_id} -> "
            f"{decision.master_patient_id} [{decision.method}, {decision.score}]"
        )