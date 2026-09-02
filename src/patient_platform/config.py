"""
Chargement de la configuration des sources.

Point unique de lecture de `config/sources.json`. Le champ `data_root`
permet de basculer le pipeline MVP/Spark sur un jeu de données différent
(ex: un répertoire d'expérience du Synthetic Patient Data Generator)
sans toucher au code :

    {
      "data_root": "synthetic-patient-generator/data/experiments/hard",
      "pharmacy": {"patient_source": "pharmacy/patients.csv", ...}
    }
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_config(config_path: str | Path = "config/sources.json") -> dict[str, Any]:
    path = Path(config_path)
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def data_root(config: dict[str, Any]) -> Path:
    """Répertoire de base des données (clé `data_root`, défaut `data/raw`)."""
    return Path(config.get("data_root", "data/raw"))


def load_sources(config_path: str | Path = "config/sources.json") -> dict[str, dict[str, Path]]:
    """
    Retourne, pour chaque source, les chemins résolus `patient_source` /
    `business_source` en préfixant par `data_root`.
    """
    config = load_config(config_path)
    root = data_root(config)
    return {
        system: {
            "patient_source": root / paths["patient_source"],
            "business_source": root / paths["business_source"],
        }
        for system, paths in config.items()
        if system != "data_root"
    }


def load_data_root(config_path: str | Path = "config/sources.json") -> Path:
    return data_root(load_config(config_path))