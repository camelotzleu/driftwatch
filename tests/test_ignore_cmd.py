"""Tests for driftwatch.commands.ignore_cmd."""
from __future__ import annotations

import argparse
import json
from unittest.mock import MagicMock, patch

import pytest

from driftwatch.commands.ignore_cmd import cmd_ignore
from driftwatch.comparator import CompareResult
from driftwatch.differ import DriftEntry, DriftReport


def _args(**kwargs):
    defaults = {
        "provider": "mock",
        "config": "driftwatch.yaml",
        "rules_file": None,
        "format": "text",
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _empty_report():
    return DriftReport()


def _drift_report():
    r = DriftReport()
    r.entries.append(
        DriftEntry(
            resource_id="i-123",
            kind="instance",
            provider="mock",
            change_type="changed",
            attribute_diff={},
        )
    )
    return r


def _mock_cfg(providers=None):
    cfg = MagicMock()
    cfg.raw = {}
    p = MagicMock()
    p.name = "mock"
    cfg.providers = providers if providers is not None else [p]
    return cfg


def test_cmd_ignore_unknown_provider():
    with patch("driftwatch.commands.ignore_cmd.load_config", return_value=_mock_cfg([])):
        rc = cmd_ignore(_args(provider="unknown"))
    assert rc == 1


def test_cmd_ignore_no_drift_text(capsys):
    ok_result = CompareResult(ok=True, message="", report=_empty_report())
    with patch("driftwatch.commands.ignore_cmd.load_config", return_value=_mock_cfg()), \
         patch("driftwatch.commands.ignore_cmd.get_collector"), \
         patch("driftwatch.commands.ignore_cmd.compare_to_baseline", return_value=ok_result):
        rc = cmd_ignore(_args())
    assert rc == 0
    out = capsys.readouterr().out
    assert "Kept:" in out
    assert "Ignored:" in out


def test_cmd_ignore_with_rule_removes_entry(capsys):
    ok_result = CompareResult(ok=True, message="", report=_drift_report())
    cfg = _mock_cfg()
    cfg.raw = {"ignore_rules": [{"resource_id": "i-123", "reason": "known"}]}
    with patch("driftwatch.commands.ignore_cmd.load_config", return_value=cfg), \
         patch("driftwatch.commands.ignore_cmd.get_collector"), \
         patch("driftwatch.commands.ignore_cmd.compare_to_baseline", return_value=ok_result):
        rc = cmd_ignore(_args())
    assert rc == 0
    out = capsys.readouterr().out
    assert "Ignored: 1" in out
    assert "known" in out


def test_cmd_ignore_json_output(capsys):
    ok_result = CompareResult(ok=True, message="", report=_empty_report())
    with patch("driftwatch.commands.ignore_cmd.load_config", return_value=_mock_cfg()), \
         patch("driftwatch.commands.ignore_cmd.get_collector"), \
         patch("driftwatch.commands.ignore_cmd.compare_to_baseline", return_value=ok_result):
        rc = cmd_ignore(_args(format="json"))
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert "kept_count" in data
    assert "ignored_count" in data
