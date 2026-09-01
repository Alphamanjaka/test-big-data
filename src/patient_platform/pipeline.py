from dataclasses import dataclass
from pathlib import Path

from patient_platform.deduplication.matcher import MatchDecision, deduplicate
from patient_platform.extract.csv_extractor import CSVExtractor
from patient_platform.extract.raw_record import RawPatientRecord
from patient_platform.logging_utils import RuntimeLogger
from patient_platform.transform.canonical import CanonicalPatient, standardize_patients


@dataclass(frozen=True)
class PipelineResult:
    raw_records: list[RawPatientRecord]
    patients: list[CanonicalPatient]
    identity_map: list[MatchDecision]


def run_pipeline(
    data_root: str | Path,
    runtime_log_path: str | Path = "logs/runtime.log",
    audit_log_path: str | Path = "LOGS.md",
) -> PipelineResult:
    logger = RuntimeLogger(runtime_log_path, audit_log_path)
    logger.info("pipeline", status="started")
    root = Path(data_root)
    sources = {
        "pharmacy": root / "pharmacy" / "patients.csv",
        "consultation": root / "consultation" / "patients.csv",
        "imaging": root / "imaging" / "patients.csv",
    }
    canonical_patients: list[CanonicalPatient] = []
    raw_records: list[RawPatientRecord] = []
    source_id_columns = {
        "pharmacy": "client_id",
        "consultation": "patient_code",
        "imaging": "id_personne",
    }
    for source_system, file_path in sources.items():
        raw_frame = CSVExtractor(file_path, source_system).extract()
        logger.info("extraction", source=source_system,
                    rows_read=len(raw_frame), status="success")
        raw_records.extend(
            RawPatientRecord(
                source_system=source_system,
                source_patient_id=str(row[source_id_columns[source_system]]),
                source_file=str(row["source_file"]),
                payload={key: str(value) for key, value in row.items()},
            )
            for _, row in raw_frame.iterrows()
        )
        canonical_patients.extend(
            standardize_patients(raw_frame, source_system))

    identity_map = deduplicate(canonical_patients)
    logger.info(
        "deduplication",
        method="exact_then_probabilistic",
        master_patients=len(
            {decision.master_patient_id for decision in identity_map}),
        identity_links=len(identity_map),
        status="success",
    )
    logger.info("pipeline", status="completed")
    return PipelineResult(raw_records, canonical_patients, identity_map)
