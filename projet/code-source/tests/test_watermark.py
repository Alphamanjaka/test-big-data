"""Tests du watermark d'ingestion (anti-retraitement en boucle)."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from provision.scripts.utils import watermark


def test_file_signature_stable_and_sensitive(tmp_path):
    a = tmp_path / "a.csv"
    b = tmp_path / "b.csv"
    a.write_text("id,prenom\n1,Alice\n", encoding="utf-8")
    b.write_text("id,prenom\n1,Alice\n", encoding="utf-8")
    sig_a1 = watermark.file_signature(str(a))
    sig_b = watermark.file_signature(str(b))
    assert sig_a1["signature"] == sig_b["signature"]
    assert sig_a1["size"] == sig_b["size"] == a.stat().st_size
    assert "mtime" in sig_a1

    a.write_text("id,prenom\n1,Alice\n2,Bob\n", encoding="utf-8")
    sig_a2 = watermark.file_signature(str(a))
    assert sig_a2["signature"] != sig_a1["signature"]


# ---------------------------------------------------------------------------
# Décision d'extraction
# ---------------------------------------------------------------------------

def _sig(x="content-v1"):
    return {"signature": x, "size": len(x), "mtime": 1.0}


def test_initial_extraction_when_no_entry():
    extract, reason = watermark.should_extract({}, "pharmacy", "patients", _sig(), "resume")
    assert extract is True
    assert reason == "initial"


def test_config_full_force_extract():
    wm = {"pharmacy": {"patients": {"last": {"signature": "content-v1"}}}}
    extract, reason = watermark.should_extract(wm, "pharmacy", "patients", _sig(), None, "full")
    assert extract is True
    assert reason == "config:full"


def test_pipeline_full_and_since_force_extract():
    wm = {"pharmacy": {"patients": {"last": {"signature": "content-v1"}}}}
    extract, reason = watermark.should_extract(wm, "pharmacy", "patients", _sig(), "full")
    assert extract is True and reason == "pipeline:full"
    extract, reason = watermark.should_extract(wm, "pharmacy", "patients", _sig(), "since")
    assert extract is True and reason == "pipeline:since"


def test_unchanged_signature_skips():
    wm = {"pharmacy": {"patients": {"last": {"signature": "content-v1"}}}}
    extract, reason = watermark.should_extract(wm, "pharmacy", "patients", _sig("content-v1"), "resume")
    assert extract is False
    assert reason == "unchanged"


def test_changed_signature_extracts():
    wm = {"pharmacy": {"patients": {"last": {"signature": "content-v1"}}}}
    extract, reason = watermark.should_extract(wm, "pharmacy", "patients", _sig("content-v2"), "resume")
    assert extract is True
    assert reason == "changed"


# ---------------------------------------------------------------------------
# Mémorisation d'un lot + reconstruction du rapport
# ---------------------------------------------------------------------------

def test_remember_and_report(tmp_path):
    # Le fichier réel du projet peut exister (écrit par un vrai run du pipeline) : on
    # vérifie qu'il n'est pas modifié par le test, et non qu'il est absent.
    real_path = watermark.watermark_path()
    before = os.path.getmtime(real_path) if os.path.exists(real_path) else None
    wm = {}
    watermark.remember(
        wm,
        "pharmacy",
        "patients",
        _sig("content-v1"),
        row_count=5,
        columns=[{"name": "id", "type": "string"}],
        sample_data=[{"id": "1"}],
        hdfs_path="hdfs://localhost:9000/datalake/raw/pharmacy/patients",
        batch_id="20260928_100000",
    )
    entry = wm["pharmacy"]["patients"]
    assert entry["last"]["signature"] == "content-v1"
    assert entry["batches"][0]["batch_id"] == "20260928_100000"

    report = watermark.report_from_watermark(wm, "pharmacy", "patients")
    assert report is not None
    assert report["skipped"] is True
    assert report["row_count"] == 5
    assert report["hdfs_path"].endswith("pharmacy/patients")

    # Isolement : remember/report travaillent en mémoire, aucun fichier réel n'est écrit.
    after = os.path.getmtime(real_path) if os.path.exists(real_path) else None
    assert after == before


def test_wiped_entry_returns_none():
    assert watermark.report_from_watermark({"x": {"t": {}}}, "x", "t") is None


def test_batches_history_capped_at_50():
    wm = {}
    for i in range(60):
        watermark.remember(wm, "s", "t", _sig("v%d" % i))
    assert len(wm["s"]["t"]["batches"]) == 50


def test_save_and_load_roundtrip(tmp_path, monkeypatch):
    path = tmp_path / "watermark.json"
    monkeypatch.setenv("PIPELINE_WATERMARK_PATH", str(path))
    watermark.save({"s": {"t": {"last": {"signature": "x"}}}})
    loaded = watermark.load()
    assert loaded["s"]["t"]["last"]["signature"] == "x"