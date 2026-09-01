from patient_platform.pipeline import run_pipeline


if __name__ == "__main__":
    result = run_pipeline("data/raw")
    for decision in result.identity_map:
        print(
            f"{decision.source_system}:{decision.source_patient_id} -> "
            f"{decision.master_patient_id} [{decision.method}, {decision.score}]"
        )
