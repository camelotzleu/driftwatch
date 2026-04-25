"""Tests for driftwatch.commands.throttle_cmd."""
from __future__ import annotations

import argparse
from unittest.mock import MagicMock, patch

import pytest

from driftwatch.commands.throttle_cmd import cmd_throttle
from driftwatch.comparator import CompareResult
from driftwatch.differ import DriftEntry, DriftReport


def _args(provider="mock", fmt="text"):
    ns = argparse.Namespace()
    ns.provider = provider
    ns.format = fmt
    return ns


def _empty_report():
    return DriftReport()


def _drift_report():
    r = DriftReport()
    r.entries.append(
        DriftEntry(
            resource_id="r1",
            kind="instance",
            provider="mock",
            change_type="changed",
            attribute_diff={},
        )
    )
    return r


def _mock_cfg():
    cfg = MagicMock()
    cfg.throttle_rules = []
    return cfg


# ---------------------------------------------------------------------------

def test_cmd_throttle_unknown_provider(capsys):
    with patch("driftwatch.commands.throttle_cmd.get_collector", side_effect=KeyError("x")):
        rc = cmd_throttle(_args(provider="bogus"), _mock_cfg())
    assert rc == 1
    captured = capsys.readouterr()
    assert "Unknown provider" in captured.err


def test_cmd_throttle_no_baseline(capsys):
    mock_collector = MagicMock()
    mock_collector.collect.return_value = MagicMock()
    no_baseline = CompareResult(ok=False, report=_empty_report())

    with patch("driftwatch.commands.throttle_cmd.get_collector", return_value=mock_collector), \
         patch("driftwatch.commands.throttle_cmd.compare_to_baseline", return_value=no_baseline):
        rc = cmd_throttle(_args(), _mock_cfg())

    assert rc == 1
    captured = capsys.readouterr()
    assert "No baseline" in captured.err


def test_cmd_throttle_no_drift_text(capsys):
    mock_collector = MagicMock()
    mock_collector.collect.return_value = MagicMock()
    ok_result = CompareResult(ok=True, report=_empty_report())

    with patch("driftwatch.commands.throttle_cmd.get_collector", return_value=mock_collector), \
         patch("driftwatch.commands.throttle_cmd.compare_to_baseline", return_value=ok_result):
        rc = cmd_throttle(_args(), _mock_cfg())

    assert rc == 0
    out = capsys.readouterr().out
    assert "Allowed" in out
    assert "Suppressed" in out


def test_cmd_throttle_json_output(capsys):
    import json
    mock_collector = MagicMock()
    mock_collector.collect.return_value = MagicMock()
    ok_result = CompareResult(ok=True, report=_empty_report())

    with patch("driftwatch.commands.throttle_cmd.get_collector", return_value=mock_collector), \
         patch("driftwatch.commands.throttle_cmd.compare_to_baseline", return_value=ok_result):
        rc = cmd_throttle(_args(fmt="json"), _mock_cfg())

    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert "allowed_count" in data
    assert "suppressed_count" in data
