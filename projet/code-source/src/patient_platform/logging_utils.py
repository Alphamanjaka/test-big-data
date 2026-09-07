from datetime import datetime, timezone
from pathlib import Path


class RuntimeLogger:
    """Journalise chaque événement dans UN SEUL fichier et l'affiche en console.

    Toute journalisation converge vers un fichier unique (par défaut `LOGS.md`,
    conforme à ai_context/logs.md) et est aussi émise sur la sortie standard.
    """

    def __init__(self, runtime_path: str | Path = "logs/runtime.log",
                 audit_path: str | Path = "LOGS.md",
                 console: bool = True):
        # Une seule destination : le fichier d'audit consolidé.
        self.log_path = Path(audit_path)
        self.console = console
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

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

        with self.log_path.open("a", encoding="utf-8") as log_file:
            log_file.write(entry + "\n")
            log_file.flush()

        if self.console:
            print(entry)
