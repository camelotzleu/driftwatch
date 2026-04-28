"""Tests for driftwatch.commands.budget_cmd."""
from __future__ import annotations

import argparse
import json
from unittest.mock import MagicMock, patch

from driftwatch.commands.budget_cmd import cmd_budget
from driftwatch.differ import DriftEntry, DriftReport
from driftwatch.comparator import CompareResult


def _args(**kwargs) -> argparse.Namespace:
    defaults = {
        "provider": "mock",
        "limit": 5,
        "priority": None,
        "format": "text",
        "config": "driftwatch.yaml",
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _entry(resource_id: str, change_type: str = "changed") -> DriftEntry:
    return DriftEntry(
        resource_id=resource_id,
        kind="Instance",
        provider="mock",
        change_type=change_type,
        attribute_diff={},
    )


def _empty_report() -> DriftReport:
    return DriftReport()


def _drift_report(*entries: DriftEntry) -> DriftReport:
    r = DriftReport()
    r.entries.extend(entries)
    return r


def _mock_cfg(provider_name: str = "mock"):
    provider = MagicMock()
    provider.name = provider_name
    cfg = MagicMock()
    cfg.providers = [provider]
    return cfg


def test_cmd_budget_unknown_provider(capsys):
    cfg = _mock_cfg("aws")
    with patch("driftwatch.commands.budget_cmd.load_config", return_value=cfg):
        rc = cmd_budget(_args(provider="nonexistent"))
    assert rc == 1
    captured = capsys.readouterr()
    assert "Unknown provider" in captured.err


def test_cmd_budget_no_baseline(capsys):
    cfg = _mock_cfg()
    snap = MagicMock()
    no_baseline = CompareResult(ok=False, report=None)
    with patch("driftwatch.commands.budget_cmd.load_config", return_value=cfg), \
         patch("driftwatch.commands.budget_cmd.get_collector") as gc, \
         patch("driftwatch.commands.budget_cmd.compare_to_baseline", return_value=no_baseline):
        gc.return_value.collect.return_value = snap
        rc = cmd_budget(_args())
    assert rc == 1
    captured = capsys.readouterr()
    assert "No baseline" in captured.err


def test_cmd_budget_within_limit_returns_0(capsys):
    cfg = _mock_cfg()
    snap = MagicMock()
    report = _drift_report(_entry("r1"), _entry("r2"))
    ok_result = CompareResult(ok=True, report=report)
    with patch("driftwatch.commands.budget_cmd.load_config", return_value=cfg), \
         patch("driftwatch.commands.budget_cmd.get_collector") as gc, \
         patch("driftwatch.commands.budget_cmd.compare_to_baseline", return_value=ok_result):
        gc.return_value.collect.return_value = snap
        rc = cmd_budget(_args(limit=10))
    assert rc == 0
    out = capsys.readouterr().out
    assert "2/10" in out


def test_cmd_budget_over_limit_returns_1(capsys):
    cfg = _mock_cfg()
    snap = MagicMock()
    report = _drift_report(_entry("r1"), _entry("r2"), _entry("r3"))
    ok_result = CompareResult(ok=True, report=report)
    with patch("driftwatch.commands.budget_cmd.load_config", return_value=cfg), \
         patch("driftwatch.commands.budget_cmd.get_collector") as gc, \
         patch("driftwatch.commands.budget_cmd.compare_to_baseline", return_value=ok_result):
        gc.return_value.collect.return_value = snap
        rc = cmd_budget(_args(limit=2))
    assert rc == 1
    out = capsys.readouterr().out
    assert "Over budget" in out


def test_cmd_budget_json_output(capsys):
    cfg = _mock_cfg()
    snap = MagicMock()
    report = _drift_report(_entry("r1", "added"))
    ok_result = CompareResult(ok=True, report=report)
    with patch("driftwatch.commands.budget_cmd.load_config", return_value=cfg), \
         patch("driftwatch.commands.budget_cmd.get_collector") as gc, \
         patch("driftwatch.commands.budget_cmd.compare_to_baseline", return_value=ok_result):
        gc.return_value.collect.return_value = snap
        rc = cmd_budget(_args(limit=5, format="json"))
    assert rc == 0
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "limit" in data
    assert "accepted" in data
    assert data["limit"] == 5
