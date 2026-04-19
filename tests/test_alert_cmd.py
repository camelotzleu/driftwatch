"""Tests for driftwatch.commands.alert_cmd."""
import json
import pytest
from unittest.mock import patch, MagicMock
from argparse import Namespace
from driftwatch.commands.alert_cmd import cmd_alert
from driftwatch.differ import DriftReport, DriftEntry
from driftwatch.snapshot import Snapshot


def _args(rules_file=None, config="driftwatch.yaml"):
    return Namespace(config=config, rules=rules_file)


def _make_report(n=1):
    r = DriftReport()
    for i in range(n):
        r.entries.append(DriftEntry(
            resource_id=f"res-{i}", resource_type="ec2",
            provider="aws", kind="changed",
            attribute_diff={},
        ))
    return r


def _mock_cfg(rules=None):
    cfg = MagicMock()
    cfg.provider.name = "aws"
    cfg.raw = {"alerting": {"rules": rules}} if rules else {}
    return cfg


@patch("driftwatch.commands.alert_cmd.config.load")
@patch("driftwatch.commands.alert_cmd.baseline.load")
@patch("driftwatch.commands.alert_cmd.get_collector")
@patch("driftwatch.commands.alert_cmd.compare")
def test_cmd_alert_no_rules_returns_1(mock_compare, mock_gc, mock_bl, mock_cfg):
    mock_cfg.return_value = _mock_cfg()
    rc = cmd_alert(_args())
    assert rc == 1


@patch("driftwatch.commands.alert_cmd.config.load")
@patch("driftwatch.commands.alert_cmd.baseline.load")
@patch("driftwatch.commands.alert_cmd.get_collector")
@patch("driftwatch.commands.alert_cmd.compare")
def test_cmd_alert_no_baseline_returns_1(mock_compare, mock_gc, mock_bl, mock_cfg):
    rules = [{"name": "r", "min_changes": 1}]
    mock_cfg.return_value = _mock_cfg(rules)
    mock_bl.return_value = None
    mock_gc.return_value.collect.return_value = MagicMock()
    rc = cmd_alert(_args())
    assert rc == 1


@patch("driftwatch.commands.alert_cmd.config.load")
@patch("driftwatch.commands.alert_cmd.baseline.load")
@patch("driftwatch.commands.alert_cmd.get_collector")
@patch("driftwatch.commands.alert_cmd.compare")
def test_cmd_alert_no_drift_returns_0(mock_compare, mock_gc, mock_bl, mock_cfg):
    rules = [{"name": "r", "min_changes": 1}]
    mock_cfg.return_value = _mock_cfg(rules)
    mock_bl.return_value = MagicMock()
    mock_gc.return_value.collect.return_value = MagicMock()
    mock_compare.return_value = DriftReport()
    rc = cmd_alert(_args())
    assert rc == 0


@patch("driftwatch.commands.alert_cmd.config.load")
@patch("driftwatch.commands.alert_cmd.baseline.load")
@patch("driftwatch.commands.alert_cmd.get_collector")
@patch("driftwatch.commands.alert_cmd.compare")
def test_cmd_alert_triggered_returns_2(mock_compare, mock_gc, mock_bl, mock_cfg):
    rules = [{"name": "r", "min_changes": 1, "severity": "critical"}]
    mock_cfg.return_value = _mock_cfg(rules)
    mock_bl.return_value = MagicMock()
    mock_gc.return_value.collect.return_value = MagicMock()
    mock_compare.return_value = _make_report(2)
    rc = cmd_alert(_args())
    assert rc == 2
