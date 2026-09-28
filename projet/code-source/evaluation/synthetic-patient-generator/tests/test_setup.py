"""
Tests de l'Étape 1 — Initialisation.

Vérifie que la structure du projet et les dépendances sont en place
avant de commencer l'Étape 2 (Patient Generator).
"""

import importlib

from config import settings


def test_directory_structure_exists():
    assert settings.DATA_DIR.exists()
    assert settings.GROUND_TRUTH_DIR.exists()
    assert settings.RAW_DIR.exists()
    assert settings.EXPERIMENTS_DIR.exists()
    assert settings.PHARMACY_DIR.exists()
    assert settings.CONSULTATION_DIR.exists()
    assert settings.IMAGING_DIR.exists()


def test_dependencies_installed():
    for module_name in ("faker", "pandas"):
        importlib.import_module(module_name)


def test_difficulty_levels_defined():
    assert set(settings.DIFFICULTY_LEVELS) == {"easy", "medium", "hard"}
    assert settings.DIFFICULTY_LEVELS["easy"] < settings.DIFFICULTY_LEVELS["hard"]


def test_sources_defined():
    assert settings.SOURCES == ["pharmacy", "consultation", "imaging"]
