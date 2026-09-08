"""Moteur de resolution d'identite patient."""

from __future__ import annotations

from engine.identity.canonical import CanonicalPatient, matching_key, _normalized, _cin, _text, _gender, _birth_date
from engine.identity.matcher import MatchDecision, deduplicate

__all__ = [
    "CanonicalPatient",
    "MatchDecision",
    "matching_key",
    "deduplicate",
    "_normalized",
    "_cin",
    "_text",
    "_gender",
    "_birth_date",
]