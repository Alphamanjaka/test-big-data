"""
Étape 4 — Variation Engine.

Cœur du projet : transforme une identité "propre" (Ground Truth) en une
identité "sale", telle qu'on la trouverait dans un vrai système métier.

Pipeline (cf. plan d'implémentation) :

    normalize -> variation -> typo -> format -> missing values

Chaque type de variation n'est appliqué qu'avec une certaine probabilité,
déterminée par le niveau de difficulté (`config.settings.DIFFICULTY_LEVELS`)
et la liste des types débloqués à ce niveau
(`config.settings.DIFFICULTY_VARIATION_TYPES`).
"""

from __future__ import annotations

import random
from datetime import date, datetime

from config import settings

# ---------------------------------------------------------------------------
# 1. Normalize — remet l'identité dans une forme canonique avant de la salir
# ---------------------------------------------------------------------------


def normalize(patient: dict) -> dict:
    """Copie défensive de l'identité propre, forme canonique de départ."""
    return {
        "first_name": patient["first_name"].strip(),
        "last_name": patient["last_name"].strip(),
        "birth_date": patient["birth_date"],  # format ISO YYYY-MM-DD attendu
        "cin": patient.get("cin"),  # CIN malgache "DDD DDDDD D" (ou None)
        "birth_city": (patient.get("birth_city") or "").strip(),
        "address": (patient.get("address") or "").strip(),
    }


# ---------------------------------------------------------------------------
# 2. Variations sur les noms
# ---------------------------------------------------------------------------


def vary_case(text: str, rng: random.Random) -> str:
    """Variation de casse : MAJUSCULES ou minuscules."""
    return rng.choice([text.upper(), text.lower()])


def vary_spacing(text: str, rng: random.Random) -> str:
    """Espaces supplémentaires : en début/fin, ou dédoublés à l'intérieur."""
    style = rng.choice(["leading", "trailing", "internal"])
    if style == "leading":
        return f" {text}"
    if style == "trailing":
        return f"{text} "
    return text.replace(" ", "  ", 1) if " " in text else text


def invert_name(first_name: str, last_name: str) -> tuple[str, str]:
    """Inversion nom/prénom : Jean Rakoto -> Rakoto Jean."""
    return last_name, first_name


def abbreviate_first_name(first_name: str) -> str:
    """Abréviation du prénom : Jean -> J."""
    return f"{first_name[0]}." if first_name else first_name


# ---------------------------------------------------------------------------
# 3. Typo — erreurs typographiques
# ---------------------------------------------------------------------------


def apply_typo(text: str, rng: random.Random) -> str:
    """
    Introduit une faute de frappe légère : suppression, duplication ou
    substitution d'un caractère (ex: Rakoto -> Rakot / Rakotoo / Rakto).
    """
    if len(text) < 3:
        return text

    position = rng.randrange(1, len(text) - 1)
    kind = rng.choice(["delete", "duplicate", "swap"])

    if kind == "delete":
        return text[:position] + text[position + 1 :]
    if kind == "duplicate":
        return text[: position + 1] + text[position] + text[position + 1 :]
    # swap deux caractères adjacents
    chars = list(text)
    chars[position], chars[position + 1] = chars[position + 1], chars[position]
    return "".join(chars)


# ---------------------------------------------------------------------------
# 4. Format — CIN et date
# ---------------------------------------------------------------------------


def vary_cin_format(cin: str, rng: random.Random) -> str:
    """
    Reformate un CIN malgache (ex: 101 024045 2) selon un des formats
    observés dans les sources : espacé, compact, ou tel quel.
    """
    if not cin:
        return cin
    digits = "".join(ch for ch in cin if ch.isdigit())  # ex: "101024045"
    style = rng.choice(["raw", "spaced", "compact"])

    if style == "raw":
        return cin
    if style == "spaced":
        return f"{digits[:3]} {digits[3:8]} {digits[8:]}"
    return digits


def vary_date_format(birth_date: str, rng: random.Random) -> str:
    """
    Reformate une date ISO (YYYY-MM-DD) selon un des formats observés
    dans les sources : DD/MM/YYYY, YYYY/MM/DD, DD-MM-YYYY, YYYY-MM-DD.
    """
    parsed: date = datetime.strptime(birth_date, "%Y-%m-%d").date()
    style = rng.choice(["dmy_slash", "ymd_slash", "dmy_dash", "ymd_dash"])

    if style == "dmy_slash":
        return parsed.strftime("%d/%m/%Y")
    if style == "ymd_slash":
        return parsed.strftime("%Y/%m/%d")
    if style == "dmy_dash":
        return parsed.strftime("%d-%m-%Y")
    return parsed.strftime("%Y-%m-%d")


# ---------------------------------------------------------------------------
# 5. Missing values
# ---------------------------------------------------------------------------


def make_missing(rng: random.Random) -> dict:
    """Choisit un champ non-identitaire à vider (birth_date ou birth_city).

    Le CIN, lui, ne passe JAMAIS par ici : son absence est une décision de
    niveau maître (~75 % de couverture), toujours cohérente entre les sources.
    """
    return {"field": rng.choice(["birth_date", "birth_city"])}


# ---------------------------------------------------------------------------
# Orchestrateur
# ---------------------------------------------------------------------------


def apply_variations(
    patient: dict,
    difficulty: str,
    rng: random.Random,
) -> dict:
    """
    Applique le pipeline complet de variations à un patient propre, selon
    le niveau de difficulté choisi ("easy", "medium", "hard").

    Retourne une nouvelle identité (potentiellement) "sale", avec en plus
    la clé `_variations_applied` listant les transformations effectuées
    (utile pour les tests et le débogage — à retirer avant export final).
    """
    if difficulty not in settings.DIFFICULTY_LEVELS:
        raise ValueError(f"Niveau de difficulté inconnu : {difficulty}")

    probability = settings.DIFFICULTY_LEVELS[difficulty]
    allowed_types = settings.DIFFICULTY_VARIATION_TYPES[difficulty]

    result = normalize(patient)
    applied: list[str] = []

    # normalize -> variation (casse, espaces, inversion, abréviation)
    if "case" in allowed_types and rng.random() < probability:
        result["first_name"] = vary_case(result["first_name"], rng)
        result["last_name"] = vary_case(result["last_name"], rng)
        applied.append("case")

    if "spacing" in allowed_types and rng.random() < probability:
        result["last_name"] = vary_spacing(result["last_name"], rng)
        applied.append("spacing")

    if "name_inversion" in allowed_types and rng.random() < probability:
        result["first_name"], result["last_name"] = invert_name(
            result["first_name"], result["last_name"]
        )
        applied.append("name_inversion")

    if "abbreviation" in allowed_types and rng.random() < probability:
        result["first_name"] = abbreviate_first_name(result["first_name"])
        applied.append("abbreviation")

    # typo
    if "typo_light" in allowed_types and rng.random() < probability:
        result["last_name"] = apply_typo(result["last_name"], rng)
        applied.append("typo_light")

    if "typo" in allowed_types and rng.random() < probability:
        result["first_name"] = apply_typo(result["first_name"], rng)
        result["last_name"] = apply_typo(result["last_name"], rng)
        applied.append("typo")

    # format
    if "cin_format" in allowed_types and result.get("cin") and rng.random() < probability:
        result["cin"] = vary_cin_format(result["cin"], rng)
        applied.append("cin_format")

    if "date_format" in allowed_types and rng.random() < probability:
        result["birth_date"] = vary_date_format(result["birth_date"], rng)
        applied.append("date_format")

    # missing values (dernière étape : peut effacer une valeur déjà reformatée)
    if "missing_value" in allowed_types and rng.random() < probability:
        target = make_missing(rng)["field"]
        result[target] = None
        applied.append("missing_value")

    result["_variations_applied"] = applied
    return result
