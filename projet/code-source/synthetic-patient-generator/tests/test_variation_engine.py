"""
Tests de l'Étape 4 — Variation Engine.
"""

import random

import pytest

from generator.variation_engine import (
    abbreviate_first_name,
    apply_typo,
    apply_variations,
    invert_name,
    vary_case,
    vary_date_format,
    vary_phone_format,
    vary_spacing,
)

SAMPLE_PATIENT = {
    "first_name": "Jean",
    "last_name": "Rakoto",
    "birth_date": "1990-01-10",
    "phone": "0341234567",
    "address": "Antananarivo",
}


def test_vary_case_changes_casing_only():
    rng = random.Random(0)
    result = vary_case("Rakoto", rng)
    assert result.lower() == "rakoto"
    assert result in ("RAKOTO", "rakoto")


def test_vary_spacing_preserves_letters():
    rng = random.Random(0)
    result = vary_spacing("Rakoto", rng)
    assert result.strip().replace(" ", "") == "Rakoto"


def test_invert_name_swaps_first_and_last():
    assert invert_name("Jean", "Rakoto") == ("Rakoto", "Jean")


def test_abbreviate_first_name():
    assert abbreviate_first_name("Jean") == "J."


def test_apply_typo_keeps_similar_length():
    rng = random.Random(0)
    result = apply_typo("Rakoto", rng)
    assert abs(len(result) - len("Rakoto")) <= 1


def test_vary_phone_format_produces_known_formats():
    rng = random.Random(0)
    seen = {vary_phone_format("0341234567", random.Random(i)) for i in range(20)}
    assert any(f.startswith("+261") for f in seen)
    assert any(f.startswith("261") and not f.startswith("+") for f in seen)
    assert any(" " in f for f in seen)


def test_vary_date_format_produces_known_formats():
    seen = {vary_date_format("1990-01-10", random.Random(i)) for i in range(20)}
    assert "10/01/1990" in seen or "1990/01/10" in seen or "10-01-1990" in seen


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_apply_variations_preserves_expected_keys(difficulty):
    rng = random.Random(1)
    result = apply_variations(SAMPLE_PATIENT, difficulty, rng)
    assert set(result) == {"first_name", "last_name", "birth_date", "phone", "address", "_variations_applied"}


def test_hard_difficulty_triggers_more_variations_than_easy_on_average():
    def count_variations(difficulty, seed):
        rng = random.Random(seed)
        return len(apply_variations(SAMPLE_PATIENT, difficulty, rng)["_variations_applied"])

    easy_total = sum(count_variations("easy", s) for s in range(200))
    hard_total = sum(count_variations("hard", s) for s in range(200))
    assert hard_total > easy_total


def test_unknown_difficulty_raises():
    with pytest.raises(ValueError):
        apply_variations(SAMPLE_PATIENT, "impossible", random.Random(0))


def test_reproducibility_with_same_seed():
    result1 = apply_variations(SAMPLE_PATIENT, "hard", random.Random(7))
    result2 = apply_variations(SAMPLE_PATIENT, "hard", random.Random(7))
    assert result1 == result2
