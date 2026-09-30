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


# ---------------------------------------------------------------------------
# Run orphelin : processus disparu ou machine redémarrée
# ---------------------------------------------------------------------------
def _running(pid=4242, boot_id="boot-A"):
    state = pipeline_state.new_state("R9", "full", pid=pid, boot_id=boot_id)
    pipeline_state.mark_step(state, "ok", "ensure_generator_data")
    pipeline_state.mark_step(state, "started", "gen_extract_raw")
    return state


def _alive(pid):
    return True


def _dead(pid):
    return False


def _boot_a():
    return "boot-A"


def test_live_run_is_not_orphan():
    state = _running()
    assert not pipeline_state.is_orphan(state, alive=_alive, boot_id=_boot_a)
    assert not pipeline_state.reconcile(state, alive=_alive, boot_id=_boot_a)
    assert state["status"] == "running"


def test_dead_process_is_orphan_and_resumable():
    state = _running()
    assert pipeline_state.effective_status(state, alive=_dead, boot_id=_boot_a) == "failed"
    assert state["status"] == "running", "effective_status ne modifie pas l'état"
    assert pipeline_state.reconcile(state, alive=_dead, boot_id=_boot_a)
    assert state["status"] == "failed"
    assert state["steps"]["gen_extract_raw"] == "failed"
    assert state["last_error"] == pipeline_state.ORPHAN_ERROR
    assert pipeline_state.resume_start(state) == "gen_extract_raw"


def test_reboot_makes_run_orphan_even_if_pid_reused():
    # Après redémarrage, le PID a pu être réattribué à un autre processus.
    state = _running(boot_id="boot-A")
    assert pipeline_state.is_orphan(state, alive=_alive, boot_id=lambda: "boot-B")


def test_state_without_pid_keeps_previous_behaviour():
    state = pipeline_state.new_state("R0", "full")  # ancien format : pas de PID
    assert not pipeline_state.is_orphan(state, alive=_dead, boot_id=_boot_a)
    assert pipeline_state.effective_status(state, alive=_dead, boot_id=_boot_a) == "running"


def test_finished_run_is_never_orphan():
    state = _running()
    pipeline_state.finish(state, "ok")
    assert not pipeline_state.reconcile(state, alive=_dead, boot_id=_boot_a)
    assert state["status"] == "ok"


def test_cli_begin_pid_then_reconcile(tmp_path, monkeypatch):
    path = _fresh(tmp_path, monkeypatch)
    assert pipeline_state.cli(["begin", "--mode", "full", "--pid", "4242"]) == 0
    assert pipeline_state.load(str(path))["pid"] == 4242

    monkeypatch.setattr(pipeline_state, "pid_alive", _alive)
    assert pipeline_state.cli(["reconcile"]) == 0
    assert pipeline_state.load(str(path))["status"] == "running"

    monkeypatch.setattr(pipeline_state, "pid_alive", _dead)
    assert pipeline_state.cli(["reconcile"]) == 0
    assert pipeline_state.load(str(path))["status"] == "failed"