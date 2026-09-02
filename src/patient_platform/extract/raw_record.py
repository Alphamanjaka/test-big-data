from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RawPatientRecord:
    source_system: str
    source_patient_id: str
    source_file: str
    payload: dict[str, Any]
