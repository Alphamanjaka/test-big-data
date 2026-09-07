from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class BusinessRecord:
    domain: str
    source_record_id: str
    source_system: str
    source_patient_id: str
    payload: dict[str, Any]
