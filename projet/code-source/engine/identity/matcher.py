"""
Déduplication par règle d'identité stricte (v2) — implémentation de référence.

Deux fiches sont réunies si et seulement si elles partagent la clé d'identité
de `engine.identity.rules` : même CIN, même genre, même date et même ville de
naissance (ou, sans CIN des deux côtés, même nom normalisé, genre, date et
ville). Aucun score ni seuil : une fiche à l'identité incomplète reste seule.

Chaque décision est explicable (méthode, score 1,0, libellé de la règle) et
porte l'identifiant du patient maître dérivé de la clé, donc identique d'un run
à l'autre. La première fiche de chaque identité, dans l'ordre fourni, est la
fiche fondatrice (`new_master`) ; les suivantes lui sont rattachées (`exact`).

La v1 (voie exacte puis score pondéré nom / date / CIN / ville, seuil 0,80) a
été abandonnée le 30/09/2026 : sur 100 000 patients, le score réunissait deux
homonymes parfaits de CIN différents. La même règle s'exécute dans Spark
(`engine.identity.spark_dedup`), avec les mêmes fonctions de `rules`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from engine.identity.canonical import CanonicalPatient
from engine.identity.rules import explanation, identity_key, master_id


@dataclass(frozen=True)
class MatchDecision:
    master_patient_id: str
    source_system: str
    source_patient_id: str
    method: str
    score: float
    explanation: str


def deduplicate(patients: Iterable[CanonicalPatient]) -> List[MatchDecision]:
    """Une décision par fiche : `new_master` (fondatrice ou identité incomplète) ou `exact`."""
    seen = set()
    decisions: List[MatchDecision] = []
    for patient in patients:
        key = identity_key(patient)
        founder = key is None or key not in seen
        if key is not None:
            seen.add(key)
        decisions.append(MatchDecision(
            master_id(key, patient.source_system, patient.source_patient_id),
            patient.source_system,
            patient.source_patient_id,
            "new_master" if founder else "exact",
            1.0,
            explanation(key, founder),
        ))
    return decisions
