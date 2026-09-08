"""
Configuration de la de-duplication — source de vérité unique des paramètres métier.

Le fichier `config/deduplication.yaml` (racine du dépôt `code-source/`) définit :
- threshold : seuil probabiliste (score >= seuil -> fusion) ;
- weights : pondération des critères (nom / birth_date / cin / birth_city) ;
- blocking.name_prefix_len : longueur du préfixe de nom pour l'index de blocage.

Fallback robuste : si le YAML est absent ou illisible, des constantes par défaut
(égales aux valeurs historiques) sont utilisées — aucun changement de comportement.
Compatibilité Python 3.8 (from __future__ import annotations), sans dépendance lourde
(cf. sentence_transformers interdit).
"""

from __future__ import annotations

import functools
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping

import yaml

DEFAULT_THRESHOLD = 0.80
DEFAULT_WEIGHTS: Mapping[str, float] = {
    "name": 0.5,
    "birth_date": 0.3,
    "cin": 0.1,
    "birth_city": 0.1,
}
DEFAULT_NAME_PREFIX_LEN = 4

_REQUIRED_WEIGHTS = ("name", "birth_date", "cin", "birth_city")


@dataclass(frozen=True)
class DedupConfig:
    threshold: float
    weights: Mapping[str, float] = field(default_factory=lambda: dict(DEFAULT_WEIGHTS))
    name_prefix_len: int = DEFAULT_NAME_PREFIX_LEN

    def weight(self, key: str) -> float:
        return float(self.weights.get(key, 0.0))


def default_config_path() -> Path:
    """Résout `config/deduplication.yaml` à la racine du dépôt code-source."""
    return Path(__file__).resolve().parent.parent.parent.parent / "config" / "deduplication.yaml"


def parse_dedup_config(data: Mapping) -> DedupConfig:
    weights = dict(DEFAULT_WEIGHTS)
    for key in _REQUIRED_WEIGHTS:
        if key in data.get("weights", {}):
            weights[key] = float(data["weights"][key])
    return DedupConfig(
        threshold=float(data.get("threshold", DEFAULT_THRESHOLD)),
        weights=weights,
        name_prefix_len=int(data.get("blocking", {}).get("name_prefix_len", DEFAULT_NAME_PREFIX_LEN)),
    )


@functools.lru_cache(maxsize=1)
def load_dedup_config(path: str | Path | None = None) -> DedupConfig:
    """Charge la configuration depuis le YAML (mis en cache).

    `path=None` -> `config/deduplication.yaml` à la racine du dépôt. Si le fichier
    est absent ou invalide, retourne la configuration par défaut (jamais d'erreur).
    """
    resolved = Path(path) if path is not None else default_config_path()
    try:
        with open(resolved, "r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
        return parse_dedup_config(data)
    except (OSError, yaml.YAMLError, TypeError, ValueError):
        return DedupConfig(threshold=DEFAULT_THRESHOLD,
                           weights=dict(DEFAULT_WEIGHTS),
                           name_prefix_len=DEFAULT_NAME_PREFIX_LEN)