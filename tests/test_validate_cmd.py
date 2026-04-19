"""Tests for validate CLI command."""
import json
import pytest
from unittest.mock import patch, MagicMock
from driftwatch.commands.validate_cmd import cmd_validate
from driftwatch.differ import DriftReport, DriftEntry
from driftwatch.snapshot import Snapshot, ResourceSnapshot


def _args(**kwargs):
    base = dict(provider="aws", config="driftwatch.yaml", format="text", rules_json=None)
    base.update(kwargs)
    return MagicMock(**base)


def _empty_report():
    return DriftReport()


def _drift_report():
    r = DriftReport()
    r.entries.append(DriftEntry(
        resource_id="i-1", kind="disk", provider="aws",
        change_type="changed", attribute_diff={},
    ))
    return r


def _mock_cfg(provider_name="aws"):
    provider = MagicMock(name=provider_name)
    cfg = MagicMock()
    cfg.providers = [provider]
    return cfg


def _snap():
    s = Snapshot(provider="aws")
    return s


def test_cmd_validate_unknown_provider(capsys):
    cfg = MagicMock(providers=[])
    with patch("driftwatch.commands.validate_cmd.load_config", return_value=cfg):
        rc = cmd_validate(_args(provider="unknown"))
    assert rc == 1


def test_cmd_validate_no_baseline(capsys):
    with patch("driftwatch.commands.validate_cmd.load_config", return_value=_mock_cfg()), \
         patch("driftwatch.commands.validate_cmd.load_baseline", return_value=None):
        rc = cmd_validate(_args())
    assert rc == 1


def test_cmd_validate_no_rules(capsys):
    with patch("driftwatch.commands.validate_cmd.load_config", return_value=_mock_cfg()), \
         patch("driftwatch.commands.validate_cmd.load_baseline", return_value=_snap()), \
         patch("driftwatch.commands.validate_cmd.get_collector") as gc, \
         patch("driftwatch.commands.validate_cmd.compare_snapshots", return_value=_empty_report()):
        gc.return_value.collect.return_value = _snap()
        rc = cmd_validate(_args(rules_json=None))
    assert rc == 1


def test_cmd_validate_passes(capsys):
    rules = json.dumps([{"field": "kind", "allowed_values": ["instance", "disk"]}])
    with patch("driftwatch.commands.validate_cmd.load_config", return_value=_mock_cfg()), \
         patch("driftwatch.commands.validate_cmd.load_baseline", return_value=_snap()), \
         patch("driftwatch.commands.validate_cmd.get_collector") as gc, \
         patch("driftwatch.commands.validate_cmd.compare_snapshots", return_value=_drift_report()):
        gc.return_value.collect.return_value = _snap()
        rc = cmd_validate(_args(rules_json=rules))
    assert rc == 0


def test_cmd_validate_fails_json_format(capsys):
    rules = json.dumps([{"field": "kind", "allowed_values": ["bucket"]}])
    with patch("driftwatch.commands.validate_cmd.load_config", return_value=_mock_cfg()), \
         patch("driftwatch.commands.validate_cmd.load_baseline", return_value=_snap()), \
         patch("driftwatch.commands.validate_cmd.get_collector") as gc, \
         patch("driftwatch.commands.validate_cmd.compare_snapshots", return_value=_drift_report()):
        gc.return_value.collect.return_value = _snap()
        rc = cmd_validate(_args(rules_json=rules, format="json"))
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["valid"] is False
    assert rc == 2
