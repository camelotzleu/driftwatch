"""Tests for driftwatch.commands.compare_cmd."""
import argparse
import pytest
from unittest.mock import patch, MagicMock

from driftwatch.commands.compare_cmd import cmd_compare
from driftwatch.comparator import CompareResult
from driftwatch.differ import DriftReport


def _args(**kw):
    defaults = dict(config="driftwatch.yaml", baseline_dir=".", format="text")
    defaults.update(kw)
    return argparse.Namespace(**defaults)


def _empty_report():
    return DriftReport(entries=[])


@patch("driftwatch.commands.compare_cmd.compare_to_baseline")
@patch("driftwatch.commands.compare_cmd.get_collector")
@patch("driftwatch.commands.compare_cmd.load_config")
def test_cmd_compare_no_baseline(mock_cfg, mock_gc, mock_cmp):
    mock_cfg.return_value = MagicMock(provider=MagicMock())
    mock_gc.return_value.collect.return_value = MagicMock()
    mock_cmp.return_value = CompareResult(report=None, baseline_missing=True)
    assert cmd_compare(_args()) == 1


@patch("driftwatch.commands.compare_cmd.compare_to_baseline")
@patch("driftwatch.commands.compare_cmd.get_collector")
@patch("driftwatch.commands.compare_cmd.load_config")
def test_cmd_compare_no_drift(mock_cfg, mock_gc, mock_cmp):
    mock_cfg.return_value = MagicMock(provider=MagicMock())
    mock_gc.return_value.collect.return_value = MagicMock()
    report = _empty_report()
    mock_cmp.return_value = CompareResult(report=report)
    assert cmd_compare(_args()) == 0


@patch("driftwatch.commands.compare_cmd.compare_to_baseline")
@patch("driftwatch.commands.compare_cmd.get_collector")
@patch("driftwatch.commands.compare_cmd.load_config")
def test_cmd_compare_drift_found(mock_cfg, mock_gc, mock_cmp):
    from driftwatch.differ import DriftEntry
    mock_cfg.return_value = MagicMock(provider=MagicMock())
    mock_gc.return_value.collect.return_value = MagicMock()
    entry = DriftEntry(resource_id="r1", kind="instance", provider="mock",
                       region="us-east-1", change_type="changed",
                       attribute_diff={"state": {"old": "running", "new": "stopped"}})
    report = DriftReport(entries=[entry])
    mock_cmp.return_value = CompareResult(report=report)
    assert cmd_compare(_args()) == 3


@patch("driftwatch.commands.compare_cmd.compare_to_baseline")
@patch("driftwatch.commands.compare_cmd.get_collector")
@patch("driftwatch.commands.compare_cmd.load_config")
def test_cmd_compare_error(mock_cfg, mock_gc, mock_cmp):
    mock_cfg.return_value = MagicMock(provider=MagicMock())
    mock_gc.return_value.collect.return_value = MagicMock()
    mock_cmp.return_value = CompareResult(report=None, error="oops")
    assert cmd_compare(_args()) == 2
