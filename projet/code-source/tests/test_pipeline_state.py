"""Tests de la mémoire de reprise (pipeline_state, CLI incluse)."""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from provision.scripts.utils import pipeline_state


def _fresh(tmp_path, monkeypatch):
    path = tmp_path / "pipeline_state.json"
    monkeypatch.setenv("PIPELINE_STATE_PATH", str(path))
    return path


def test_new_state_statuses_and_resume_start(tmp_path, monkeypatch):
    path = _fresh(tmp_path, monkeypatch)
    state = pipeline_state.new_state("R1", "resume", start_at=0)
    assert state["status"] == "running"
    assert all(v == "pending" for v in state["steps"].values())
    assert pipeline_state.resume_start(state) == "ensure_generator_data"
    pipeline_state.save(state)
    assert pipeline_state.load(str(path))["run_id"] == "R1"


def test_start_at_inherits_prior_steps():
    state = pipeline_state.new_state("R1", "full", start_at=2)
    assert state["steps"]["ensure_generator_data"] == "ok"
    assert state["steps"]["gen_extract_raw"] == "ok"
    assert state["steps"]["gen_fhir_mapping"] == "pending"
    assert state["last_ok_step"] == "gen_extract_raw"


def test_mark_ok_then_resume():
    state = pipeline_state.new_state("R1", "resume")
    pipeline_state.mark_step(state, "ok", "ensure_generator_data")
    pipeline_state.mark_step(state, "failed", "gen_extract_raw", "code 1")
    assert pipeline_state.resume_start(state) == "gen_extract_raw"
    pipeline_state.finish(state, "failed")
    assert state["status"] == "failed"
    assert state["last_failed_step"] == "gen_extract_raw"
    assert "code 1" in state["last_error"]


def test_all_ok_means_nothing_to_resume():
    state = pipeline_state.new_state("R1", "full")
    for step in pipeline_state.STEPS:
        pipeline_state.mark_step(state, "ok", step)
    assert pipeline_state.resume_start(state) == ""


def test_cli_begin_step_finish_roundtrip(tmp_path, monkeypatch):
    path = _fresh(tmp_path, monkeypatch)
    assert pipeline_state.cli(["begin", "--mode", "resume"]) == 0
    assert pipeline_state.cli(["step", "ok", "ensure_generator_data"]) == 0
    assert pipeline_state.cli(["step", "ok", "gen_extract_raw"]) == 0
    assert pipeline_state.cli(["finish", "failed"]) == 0

    state = pipeline_state.load(str(path))
    assert state["status"] == "failed"
    assert state["steps"]["gen_extract_raw"] == "ok"
    assert pipeline_state.cli(["resume_start"]) == 0