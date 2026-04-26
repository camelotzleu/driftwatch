"""Tests for driftwatch.commands.snooze_cmd."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from driftwatch.commands.snooze_cmd import (
    cmd_snooze_add,
    cmd_snooze_apply,
    cmd_snooze_clear,
    cmd_snooze_show,
)
from driftwatch.differ import DriftEntry, DriftReport
from driftwatch.differ_snoozer import SnoozeRule, save_rules


def _future(hours: int = 24) -> str:
    return (datetime.now(timezone.utc) + timedelta(hours=hours)).isoformat()


def _args(**kwargs) -> argparse.Namespace:
    defaults = {"resource_id": "res-1", "hours": 24, "reason": "", "kind": None, "provider": None, "format": "text"}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _empty_report() -> DriftReport:
    return DriftReport()


def _drift_report() -> DriftReport:
    r = DriftReport()
    r.entries.append(
        DriftEntry(resource_id="res-1", kind="instance", provider="aws", change_type="changed", attribute_diff={})
    )
    return r


def test_cmd_snooze_add_creates_rule(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    rc = cmd_snooze_add(_args(resource_id="res-42", hours=6))
    assert rc == 0
    from driftwatch.differ_snoozer import load_rules
    rules = load_rules(directory=str(tmp_path))
    assert len(rules) == 1
    assert rules[0].resource_id == "res-42"
    assert not rules[0].is_expired()


def test_cmd_snooze_show_no_rules(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    rc = cmd_snooze_show(_args())
    assert rc == 0
    out = capsys.readouterr().out
    assert "No active" in out


def test_cmd_snooze_show_active_rule(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    rules = [SnoozeRule(resource_id="res-1", until=_future(), reason="maint")]
    save_rules(rules, directory=str(tmp_path))
    rc = cmd_snooze_show(_args())
    assert rc == 0
    out = capsys.readouterr().out
    assert "res-1" in out


def test_cmd_snooze_clear(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    rules = [SnoozeRule(resource_id="res-1", until=_future())]
    save_rules(rules, directory=str(tmp_path))
    rc = cmd_snooze_clear(_args())
    assert rc == 0
    from driftwatch.differ_snoozer import load_rules
    assert load_rules(directory=str(tmp_path)) == []


def test_cmd_snooze_apply_no_baseline(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    mock_cfg = MagicMock()
    mock_cfg.provider = "mock"
    mock_cfg.provider_config = MagicMock()
    with patch("driftwatch.commands.snooze_cmd.load_config", return_value=mock_cfg), \
         patch("driftwatch.commands.snooze_cmd.baseline.load", return_value=None), \
         patch("driftwatch.commands.snooze_cmd.get_collector") as gc:
        gc.return_value = MagicMock()
        gc.return_value.collect.return_value = MagicMock()
        rc = cmd_snooze_apply(_args())
    assert rc == 1


def test_cmd_snooze_apply_all_snoozed_returns_0(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    report = _drift_report()
    rules = [SnoozeRule(resource_id="res-1", until=_future())]
    save_rules(rules, directory=str(tmp_path))
    mock_cfg = MagicMock()
    mock_cfg.provider = "mock"
    mock_cfg.provider_config = MagicMock()
    with patch("driftwatch.commands.snooze_cmd.load_config", return_value=mock_cfg), \
         patch("driftwatch.commands.snooze_cmd.baseline.load", return_value=MagicMock()), \
         patch("driftwatch.commands.snooze_cmd.get_collector") as gc, \
         patch("driftwatch.commands.snooze_cmd.differ.diff", return_value=report):
        gc.return_value = MagicMock()
        gc.return_value.collect.return_value = MagicMock()
        rc = cmd_snooze_apply(_args())
    assert rc == 0
