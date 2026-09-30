"""Tests de la règle d'identité stricte (v2) : aucune fusion sans champs identiques."""

import random
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.identity.canonical import CanonicalPatient, _cin, _text  # noqa: E402
from engine.identity.matcher import deduplicate  # noqa: E402
from engine.identity.rules import (  # noqa: E402
    EXPLANATION_INCOMPLETE, ID_LENGTH, ID_PREFIX, identity_key, master_id,
)


def _patient(source_system, source_patient_id, full_name, birth_date, cin, birth_city, gender="F"):
    return CanonicalPatient(
        source_system=source_system,
        source_patient_id=source_patient_id,
        first_name=full_name.split(" ")[0],
        last_name=full_name.split(" ", 1)[1] if " " in full_name else "",
        full_name=full_name,
        birth_date=date.fromisoformat(birth_date) if birth_date else None,
        cin=_cin(cin),
        birth_city=_text(birth_city),
        address="",
        gender=gender,
        source_file="",
    )


def _masters(patients):
    return {(d.source_system, d.source_patient_id): d.master_patient_id for d in deduplicate(patients)}


def _same(patients):
    return len(set(_masters(patients).values())) == 1


def test_same_cin_gender_date_city_merges_even_if_names_differ():
    # Faute de frappe et inversion du nom : les quatre champs d'identité suffisent.
    p1 = _patient("pharmacy", "PH001", "Jean Rakoto", "1990-05-12", "101 02404 5", "Antananarivo", "M")
    p2 = _patient("consultation", "MED001", "Rakotto Jean", "1990-05-12", "101024045", "ANTANANARIVO", "M")
    assert _same([p1, p2])
    decisions = deduplicate([p1, p2])
    assert [d.method for d in decisions] == ["new_master", "exact"]
    assert all(d.score == 1.0 for d in decisions)


def test_different_cin_never_merges():
    # Homonymes parfaits du test à 100 000 patients : même nom, même date, CIN différents.
    p1 = _patient("pharmacy", "PH014461", "Georges Grenier", "2022-04-27", "106867407", "Leclercq-la-Forêt", "M")
    p2 = _patient("pharmacy", "PH014926", "Georges Grenier", "2022-04-27", "106388848", "BonninVille", "M")
    assert not _same([p1, p2])


def test_different_gender_never_merges():
    p1 = _patient("pharmacy", "PH001", "Dominique Rabe", "1990-05-12", "101024045", "Toamasina", "M")
    p2 = _patient("imaging", "IMG001", "Dominique Rabe", "1990-05-12", "101024045", "Toamasina", "F")
    assert not _same([p1, p2])


def test_different_birth_date_or_city_never_merges():
    base = _patient("pharmacy", "PH001", "Jean Rakoto", "1990-05-12", "101024045", "Antananarivo", "M")
    other_date = _patient("consultation", "MED001", "Jean Rakoto", "1990-05-13", "101024045", "Antananarivo", "M")
    other_city = _patient("imaging", "IMG001", "Jean Rakoto", "1990-05-12", "101024045", "Fianarantsoa", "M")
    assert not _same([base, other_date])
    assert not _same([base, other_city])


def test_missing_field_means_incomplete_identity_and_no_merge():
    p1 = _patient("pharmacy", "PH001", "Jean Rakoto", "1990-05-12", "101024045", "", "M")
    p2 = _patient("consultation", "MED001", "Jean Rakoto", "1990-05-12", "101024045", "", "M")
    p3 = _patient("imaging", "IMG001", "Jean Rakoto", "", "101024045", "Antananarivo", "M")
    assert identity_key(p1) is None and identity_key(p3) is None
    decisions = deduplicate([p1, p2, p3])
    assert len({d.master_patient_id for d in decisions}) == 3
    assert all(d.method == "new_master" and d.explanation == EXPLANATION_INCOMPLETE for d in decisions)


def test_without_cin_the_name_must_also_be_identical():
    p1 = _patient("pharmacy", "PH001", "Hery Rasoa", "1975-05-02", "", "Mahajanga", "F")
    p2 = _patient("imaging", "IMG001", "HERY  RASOA", "1975-05-02", "", "mahajanga", "F")
    p3 = _patient("consultation", "MED001", "Hery Rasoanirina", "1975-05-02", "", "Mahajanga", "F")
    masters = _masters([p1, p2, p3])
    assert masters[("pharmacy", "PH001")] == masters[("imaging", "IMG001")]
    assert masters[("consultation", "MED001")] != masters[("pharmacy", "PH001")]


def test_cin_on_one_side_only_never_merges():
    # Cas « Émile Marty » : CIN absent d'un côté ; même nom, même date, ville identique ici.
    p1 = _patient("pharmacy", "PH049519", "Émile Marty", "1988-02-27", "", "Fischernec", "M")
    p2 = _patient("pharmacy", "PH058109", "Émile Marty", "1988-02-27", "122985195", "Fischernec", "M")
    assert not _same([p1, p2])


def test_master_id_is_derived_from_key_and_order_independent():
    patients = [
        _patient("pharmacy", "PH001", "Jean Rakoto", "1990-05-12", "101024045", "Antananarivo", "M"),
        _patient("consultation", "MED001", "Rakoto Jean", "1990-05-12", "101024045", "Antananarivo", "M"),
        _patient("imaging", "IMG001", "Hery Rasoa", "1975-05-02", "", "Mahajanga", "F"),
        _patient("imaging", "IMG002", "Solo Vola", "", "", "", "F"),
    ]
    reference = _masters(patients)
    shuffled = list(patients)
    random.Random(7).shuffle(shuffled)
    assert _masters(shuffled) == reference
    mid = reference[("pharmacy", "PH001")]
    assert mid.startswith(ID_PREFIX) and len(mid) == len(ID_PREFIX) + ID_LENGTH
    assert mid == master_id(identity_key(patients[0]), "pharmacy", "PH001")


def test_master_id_uses_secret_when_configured(monkeypatch):
    key = ("cin", "101024045", "M", "1990-05-12", "antananarivo")
    monkeypatch.delenv("PATIENT_ID_SECRET", raising=False)
    plain = master_id(key, "pharmacy", "PH001")
    monkeypatch.setenv("PATIENT_ID_SECRET", "secret-de-test")
    assert master_id(key, "pharmacy", "PH001") != plain


def test_spark_identity_function_matches_python_rule():
    # La fonction appelée par l'UDF Spark donne la même clé et le même identifiant.
    from engine.identity.canonical import from_dict
    from engine.identity.spark_dedup import _identity

    row = {"source_system": "pharmacy", "source_patient_id": "pharmacy_PH001", "full_name": "Jean Rakoto",
           "birth_date": "1990-05-12", "cin": "101 02404 5", "birth_city": "Antananarivo", "gender": "male"}
    key_text, mid, rule = _identity(row["source_system"], row["source_patient_id"], row["full_name"],
                                    date(1990, 5, 12), row["cin"], row["birth_city"], row["gender"])
    patient = from_dict(row)
    assert key_text == "|".join(identity_key(patient))
    assert mid == master_id(identity_key(patient), "pharmacy", "pharmacy_PH001")
    assert rule == "cin"
