"""Tests for driftwatch.commands.silence_cmd."""
import argparse
import json
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from driftwatch.commands.silence_cmd import cmd_silence
from driftwatch.comparator import CompareResult
from driftwatch.differ import DriftEntry, DriftReport


def _future():
    return (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()


def _args(**kwargs):
    defaults = {
        "provider": "mock",
        "rules_file": None,
        "format": "text",
        "config": "driftwatch.yaml",
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _empty_report():
    return DriftReport()


def _drift_report():
    r = DriftReport()
    r.entries.append(
        DriftEntry(resource_id="r-1", kind="instance", provider="mock",
                   change_type="changed", attribute_diff={})
    )
    return r


def _mock_cfg(provider_name="mock"):
    provider = MagicMock()
    provider.name = provider_name
    cfg = MagicMock()
    cfg.providers = [provider]
    cfg.silence_rules = []
    return cfg


@patch("driftwatch.commands.silence_cmd.load_config")
@patch("driftwatch.commands.silence_cmd.get_collector")
@patch("driftwatch.commands.silence_cmd.compare_to_baseline")
def test_cmd_silence_unknown_provider(mock_cmp, mock_gc, mock_lc):
    mock_lc.return_value = _mock_cfg("aws")
    rc = cmd_silence(_args(provider="gcp"))
    assert rc == 1


@patch("driftwatch.commands.silence_cmd.load_config")
@patch("driftwatch.commands.silence_cmd.get_collector")
@patch("driftwatch.commands.silence_cmd.compare_to_baseline")
def test_cmd_silence_no_baseline_returns_1(mock_cmp, mock_gc, mock_lc):
    mock_lc.return_value = _mock_cfg()
    mock_gc.return_value.collect.return_value = MagicMock()
    mock_cmp.return_value = CompareResult(ok=False, report=_empty_report())
    rc = cmd_silence(_args())
    assert rc == 1


@patch("driftwatch.commands.silence_cmd.load_config")
@patch("driftwatch.commands.silence_cmd.get_collector")
@patch("driftwatch.commands.silence_cmd.compare_to_baseline")
def test_cmd_silence_no_drift_text(mock_cmp, mock_gc, mock_lc, capsys):
    mock_lc.return_value = _mock_cfg()
    mock_gc.return_value.collect.return_value = MagicMock()
    mock_cmp.return_value = CompareResult(ok=True, report=_empty_report())
    rc = cmd_silence(_args(format="text"))
    assert rc == 0
    out = capsys.readouterr().out
    assert "Active entries" in out


@patch("driftwatch.commands.silence_cmd.load_config")
@patch("driftwatch.commands.silence_cmd.get_collector")
@patch("driftwatch.commands.silence_cmd.compare_to_baseline")
def test_cmd_silence_json_output(mock_cmp, mock_gc, mock_lc, capsys):
    mock_lc.return_value = _mock_cfg()
    mock_gc.return_value.collect.return_value = MagicMock()
    mock_cmp.return_value = CompareResult(ok=True, report=_drift_report())
    rc = cmd_silence(_args(format="json"))
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert "active_count" in data
    assert "silenced_count" in data


@patch("driftwatch.commands.silence_cmd.load_config")
@patch("driftwatch.commands.silence_cmd.get_collector")
@patch("driftwatch.commands.silence_cmd.compare_to_baseline")
def test_cmd_silence_rules_file(mock_cmp, mock_gc, mock_lc, tmp_path, capsys):
    mock_lc.return_value = _mock_cfg()
    mock_gc.return_value.collect.return_value = MagicMock()
    mock_cmp.return_value = CompareResult(ok=True, report=_drift_report())

    rules_file = tmp_path / "rules.json"
    rules_file.write_text(json.dumps([{"resource_id": "r-1", "until": _future()}]))

    rc = cmd_silence(_args(rules_file=str(rules_file), format="text"))
    assert rc == 0
    out = capsys.readouterr().out
    assert "silenced" in out.lower()
