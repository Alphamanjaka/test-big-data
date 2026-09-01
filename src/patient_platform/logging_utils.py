from datetime import datetime, timezone
from pathlib import Path


class RuntimeLogger:
    """Writes structured runtime events immediately to operational and audit logs."""

    def __init__(self, runtime_path: str | Path = "logs/runtime.log", audit_path: str | Path = "LOGS.md"):
        self.runtime_path = Path(runtime_path)
        self.audit_path = Path(audit_path)
        self.runtime_path.parent.mkdir(parents=True, exist_ok=True)
        self.audit_path.parent.mkdir(parents=True, exist_ok=True)

    def info(self, step: str, **fields: object) -> None:
        self.write("INFO", step, fields)

    def warning(self, step: str, **fields: object) -> None:
        self.write("WARNING", step, fields)

    def error(self, step: str, **fields: object) -> None:
        self.write("ERROR", step, fields)

    def write(self, level: str, step: str, fields: dict[str, object]) -> None:
        timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        values = " | ".join(f"{key}={value}" for key, value in fields.items())
        entry = f"{timestamp} | {level} | {step}"
        if values:
            entry = f"{entry} | {values}"

        with self.runtime_path.open("a", encoding="utf-8") as runtime_file:
            runtime_file.write(entry + "\n")
            runtime_file.flush()

        with self.audit_path.open("a", encoding="utf-8") as audit_file:
            audit_file.write(entry + "\n")
            audit_file.flush()
