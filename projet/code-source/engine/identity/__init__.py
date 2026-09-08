"""Moteur de resolution d'identite patient."""

from __future__ import annotations

from engine.identity.canonical import CanonicalPatient, matching_key, _normalized, _cin, _text, _gender, _birth_date
from engine.identity.matcher import MatchDecision, deduplicate
from engine.identity.config import DedupConfig, load_dedup_config

__all__ = [
    "CanonicalPatient",
    "MatchDecision",
    "DedupConfig",
    "matching_key",
    "deduplicate",
    "load_dedup_config",
    "_normalized",
    "_cin",
    "_text",
    "_gender",
    "_birth_date",
]