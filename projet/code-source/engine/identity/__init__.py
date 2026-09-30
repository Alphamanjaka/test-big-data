"""Moteur de resolution d'identite patient."""

from __future__ import annotations

from engine.identity.canonical import CanonicalPatient, _normalized, _cin, _text, _gender, _birth_date
from engine.identity.matcher import MatchDecision, deduplicate
from engine.identity.rules import identity_key, master_id

__all__ = [
    "CanonicalPatient",
    "MatchDecision",
    "identity_key",
    "master_id",
    "deduplicate",
    "_normalized",
    "_cin",
    "_text",
    "_gender",
    "_birth_date",
]
