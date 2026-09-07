from pathlib import Path

import pandas as pd


class CSVExtractor:
    """Extracts a synthetic source file while keeping source context explicit."""

    def __init__(self, file_path: str | Path, source_system: str):
        self.file_path = Path(file_path)
        self.source_system = source_system

    def extract(self) -> pd.DataFrame:
        if not self.file_path.exists():
            raise FileNotFoundError(f"Source file not found: {self.file_path}")
        frame = pd.read_csv(self.file_path, dtype=str).fillna("")
        frame["source_system"] = self.source_system
        frame["source_file"] = self.file_path.name
        return frame
