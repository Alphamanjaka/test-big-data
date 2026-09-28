"""Tests de la logique pure de planification (schedule_logic + scheduler).

Le scheduler ne nécessite ni Spark ni PyYAML (mini-lecteur YAML) : la fraction
testée ici est la décision d'échéance (daily/weekly/monthly), la non-répétition
d'une échéance déjà déclenchée et la construction des drapeaux de run.
"""

import datetime
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from provision.scripts.scheduler import scheduler as sched
from provision.scripts.utils import schedule_logic as logic

NOW = datetime.datetime(2026, 9, 28, 10, 0)  # lundi, 10:00


# ---------------------------------------------------------------------------
# Validation de la configuration
# ---------------------------------------------------------------------------

def test_defaults_are_disabled_and_daily():
    cfg = logic.validate_schedule({})
    assert cfg["enabled"] is False
    assert cfg["frequency"] == "daily"
    assert cfg["time"] == "03:00"
    assert cfg["resume"]["mode"] == "auto"


def test_validate_rejects_unknown_frequency():
    with pytest.raises(ValueError, match="frequency"):
        logic.validate_schedule({"frequency": "yearly"})


def test_validate_rejects_bad_time():
    with pytest.raises(ValueError, match="time"):
        logic.validate_schedule({"time": "25:99"})


def test_validate_rejects_bad_resume_mode():
    with pytest.raises(ValueError, match="resume.mode"):
        logic.validate_schedule({"resume": {"mode": "jamais"}})


def test_validate_requires_since_when_mode_since():
    with pytest.raises(ValueError, match="since"):
        logic.validate_schedule({"resume": {"mode": "since"}})
    cfg = logic.validate_schedule({"resume": {"mode": "since", "since": "2026-09-01"}})
    assert cfg["resume"]["since"] == "2026-09-01"


# ---------------------------------------------------------------------------
# Échéances
# ---------------------------------------------------------------------------

def _daily(time="03:00"):
    return logic.validate_schedule({"enabled": True, "frequency": "daily", "time": time})


def test_daily_past_and_next():
    cfg = _daily()
    assert logic.current_slot(NOW, cfg) == datetime.datetime(2026, 9, 28, 3, 0)
    assert logic.next_slot(NOW, cfg) == datetime.datetime(2026, 9, 29, 3, 0)


def test_daily_not_yet_reached():
    cfg = _daily("12:00")
    assert logic.current_slot(NOW, cfg) is None
    assert logic.next_slot(NOW, cfg) == datetime.datetime(2026, 9, 28, 12, 0)


def test_weekly_rollover_to_previous_week():
    cfg = logic.validate_schedule(
        {"frequency": "weekly", "time": "03:00", "day_of_week": 0}  # lundi
    )
    wednesday = datetime.datetime(2026, 9, 30, 10, 0)
    assert logic.current_slot(wednesday, cfg) == datetime.datetime(2026, 9, 28, 3, 0)
    assert logic.next_slot(wednesday, cfg) == datetime.datetime(2026, 10, 5, 3, 0)


def test_monthly_clamped_to_last_day():
    cfg = logic.validate_schedule(
        {"frequency": "monthly", "time": "03:00", "day_of_month": 31}
    )
    # Septembre n'a que 30 jours : l'échéance du mois en cours est le 30 à 03:00,
    # pas encore atteinte le 28 -> la dernière échéance passée est le 31 août.
    assert logic.current_slot(NOW, cfg) == datetime.datetime(2026, 8, 31, 3, 0)
    assert logic.next_slot(NOW, cfg) == datetime.datetime(2026, 9, 30, 3, 0)

    # Une fois l'échéance atteinte (le 30 à 10:00), elle devient courante.
    end = datetime.datetime(2026, 9, 30, 10, 0)
    assert logic.current_slot(end, cfg) == datetime.datetime(2026, 9, 30, 3, 0)
    assert logic.next_slot(end, cfg) == datetime.datetime(2026, 10, 31, 3, 0)


# ---------------------------------------------------------------------------
# Décision de lancement (anti-double déclenchement)
# ---------------------------------------------------------------------------

def test_should_launch_disabled():
    ok, reason, _ = logic.should_launch({}, NOW, logic.validate_schedule({}))
    assert ok is False
    assert "désactivée" in reason


def test_should_launch_when_slot_reached():
    ok, reason, slot = logic.should_launch({}, NOW, _daily())
    assert ok is True
    assert slot == datetime.datetime(2026, 9, 28, 3, 0)


def test_should_launch_already_launched_same_slot():
    state = {"last_launched_slot": datetime.datetime(2026, 9, 28, 3, 0).isoformat()}
    ok, reason, _ = logic.should_launch(state, NOW, _daily())
    assert ok is False
    assert "déjà" in reason


def test_should_launch_ok_for_next_day():
    state = {"last_launched_slot": datetime.datetime(2026, 9, 28, 3, 0).isoformat()}
    tomorrow = datetime.datetime(2026, 9, 29, 10, 0)
    ok, reason, _ = logic.should_launch(state, tomorrow, _daily())
    assert ok is True


# ---------------------------------------------------------------------------
# Drapeaux de lancement
# ---------------------------------------------------------------------------

def test_flags_auto_resume():
    assert logic.build_run_flags(logic.validate_schedule({})) == ["--resume"]


def test_flags_since():
    cfg = logic.validate_schedule({"resume": {"mode": "since", "since": "2026-09-01"}})
    assert logic.build_run_flags(cfg) == ["--since", "2026-09-01"]


def test_flags_full():
    cfg = logic.validate_schedule({"resume": {"mode": "full"}})
    assert logic.build_run_flags(cfg) == ["--full"]


# ---------------------------------------------------------------------------
# scheduler : lecture YAML maison et --check / --dry-run / --status
# ---------------------------------------------------------------------------

def _write(tmp_path, content):
    p = tmp_path / "schedule.yaml"
    p.write_text(content, encoding="utf-8")
    return p


def test_load_schedule_missing_file_is_disabled(tmp_path, monkeypatch):
    monkeypatch.setenv("SCHEDULE_PATH", str(tmp_path / "absent.yaml"))
    cfg = sched.load_schedule()
    assert cfg["enabled"] is False
    assert cfg["frequency"] == "daily"


def test_load_schedule_mini_yaml(tmp_path, monkeypatch):
    path = _write(
        tmp_path,
        "# commentaire\n"
        "enabled: true\n"
        "frequency: weekly\n"
        "time: \"05:30\"\n"
        "day_of_week: 2\n"
        "resume:\n"
        "  mode: since\n"
        "  since: 2026-09-01\n",
    )
    monkeypatch.setenv("SCHEDULE_PATH", str(path))
    cfg = sched.load_schedule()
    assert cfg["enabled"] is True
    assert cfg["frequency"] == "weekly"
    assert cfg["time"] == "05:30"
    assert cfg["day_of_week"] == 2
    assert cfg["resume"]["mode"] == "since"
    assert cfg["resume"]["since"] == "2026-09-01"


def test_check_disabled_does_not_launch(tmp_path, monkeypatch):
    path = _write(tmp_path, "enabled: false\n")
    monkeypatch.setenv("SCHEDULE_PATH", str(path))
    monkeypatch.setenv("SCHEDULER_STATE_PATH", str(tmp_path / "state.json"))
    monkeypatch.setenv("PIPELINE_STATE_PATH", str(tmp_path / "pipeline.json"))
    monkeypatch.setenv("RUN_PIPELINE_CMD", "echo pipeline")
    assert sched.check() == 0
    assert not (tmp_path / "state.json").exists(), "pas de déclenchement si désactivé"


def test_check_launches_once_and_persists(tmp_path, monkeypatch):
    # Échéance ce matin à 03:00, maintenant = 10:00 -> lancement attendu.
    path = _write(tmp_path, "enabled: true\nfrequency: daily\ntime: \"03:00\"\n")
    monkeypatch.setenv("SCHEDULE_PATH", str(path))
    state_file = tmp_path / "state.json"
    monkeypatch.setenv("SCHEDULER_STATE_PATH", str(state_file))
    monkeypatch.setenv("PIPELINE_STATE_PATH", str(tmp_path / "pipeline.json"))
    monkeypatch.setenv("RUN_PIPELINE_CMD", "echo pipeline")

    assert sched.check(now=NOW) == 0
    assert state_file.exists()
    state = sched.load_scheduler_state(str(state_file))
    assert state["last_launched_slot"] == datetime.datetime(2026, 9, 28, 3, 0).isoformat()

    # Deuxième appel dans la même fenêtre : plus rien à lancer.
    assert sched.check(now=NOW) == 0
    state = sched.load_scheduler_state(str(state_file))
    assert len(state["runs"]) == 1, "une seule échéance déclenchée (anti-boucle)"


def test_check_skips_when_pipeline_running(tmp_path, monkeypatch):
    path = _write(tmp_path, "enabled: true\n")
    monkeypatch.setenv("SCHEDULE_PATH", str(path))
    monkeypatch.setenv("SCHEDULER_STATE_PATH", str(tmp_path / "state.json"))
    pipeline = tmp_path / "pipeline.json"
    pipeline.write_text('{"status": "running"}', encoding="utf-8")
    monkeypatch.setenv("PIPELINE_STATE_PATH", str(pipeline))
    monkeypatch.setenv("RUN_PIPELINE_CMD", "echo pipeline")
    assert sched.check(now=NOW) == 0
    assert not (tmp_path / "state.json").exists(), "pas de double run pendant un run"


def test_dry_run_no_side_effects(tmp_path, monkeypatch):
    path = _write(tmp_path, "enabled: true\n")
    monkeypatch.setenv("SCHEDULE_PATH", str(path))
    monkeypatch.setenv("SCHEDULER_STATE_PATH", str(tmp_path / "state.json"))
    monkeypatch.setenv("PIPELINE_STATE_PATH", str(tmp_path / "pipeline.json"))
    monkeypatch.setenv("RUN_PIPELINE_CMD", "echo pipeline")
    assert sched.dry_run(now=NOW) == 0
    assert not (tmp_path / "state.json").exists()