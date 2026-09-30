"""Règle d'identité stricte (v2) : aucune fusion sans champs d'identité identiques.

Deux fiches désignent la même personne si et seulement si elles ont la même clé :
- CIN présent : même CIN, même genre, même date de naissance, même ville de
  naissance (normalisée) ;
- CIN absent des deux côtés : même nom normalisé, même genre, même date et même
  ville de naissance.

Il n'y a ni score, ni seuil, ni poids : une valeur manquante (genre, date, ville,
ou nom faute de CIN) n'est jamais « identique », et la fiche reste seule. Deux CIN
différents ne peuvent donc jamais être réunis.

L'identifiant du patient maître est dérivé de la clé (SHA-256) : il est le même
à chaque run, quel que soit l'ordre de traitement, et Spark peut le calculer
fiche par fiche sans numérotation globale. Comme la clé contient des données
identifiantes, un secret `PATIENT_ID_SECRET` (variable d'environnement) permet
d'en faire un HMAC ; sans lui (données synthétiques de démonstration), c'est une
empreinte simple, qu'une personne connaissant le genre, la date et la ville
d'un patient pourrait rapprocher de son CIN par force brute.
"""

from __future__ import annotations

import hashlib
import hmac
import os
from typing import Optional, Tuple

from engine.identity.canonical import CanonicalPatient, _normalized

ID_PREFIX = "PAT-"
ID_LENGTH = 20  # caractères hexadécimaux (80 bits) : collision négligeable à des millions de patients

EXPLANATION_CIN = "CIN, genre, date et ville de naissance identiques"
EXPLANATION_NAME = "sans CIN : nom, genre, date et ville de naissance identiques"
EXPLANATION_INCOMPLETE = "identité incomplète (genre, date ou ville manquant) : aucune fusion"
EXPLANATION_FOUNDER = "première fiche de cette identité"


def identity_key(patient: CanonicalPatient) -> Optional[Tuple[str, ...]]:
    """Clé d'identité stricte, ou None si un champ requis manque."""
    gender = patient.gender if patient.gender in ("M", "F") else ""
    birth = patient.birth_date.isoformat() if patient.birth_date else ""
    city = _normalized(patient.birth_city)
    if not (gender and birth and city):
        return None
    if patient.cin:
        return ("cin", patient.cin, gender, birth, city)
    name = _normalized(patient.full_name)
    if not name:
        return None
    return ("nom", name, gender, birth, city)


def master_id(key: Optional[Tuple[str, ...]], source_system: str, source_patient_id: str) -> str:
    """Identifiant du patient maître : empreinte de la clé, ou de la fiche si la clé manque."""
    basis = "|".join(key) if key else "|".join(("fiche", source_system, source_patient_id))
    secret = os.environ.get("PATIENT_ID_SECRET", "")
    if secret:
        digest = hmac.new(secret.encode("utf-8"), basis.encode("utf-8"), hashlib.sha256).hexdigest()
    else:
        digest = hashlib.sha256(basis.encode("utf-8")).hexdigest()
    return ID_PREFIX + digest[:ID_LENGTH].upper()


def explanation(key: Optional[Tuple[str, ...]], founder: bool) -> str:
    """Libellé explicable d'une décision : fiche fondatrice, rattachement ou identité incomplète."""
    if key is None:
        return EXPLANATION_INCOMPLETE
    rule = EXPLANATION_CIN if key[0] == "cin" else EXPLANATION_NAME
    return f"{EXPLANATION_FOUNDER} ({rule})" if founder else rule
