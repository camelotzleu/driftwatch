"""Tests for driftwatch.commands.classify_cmd."""
import argparse
from unittest.mock import patch, MagicMock
from driftwatch.commands.classify_cmd import cmd_classify
from driftwatch.differ import DriftReport, DriftEntry
from driftwatch.comparator import CompareResult


def _args(provider="aws", fmt="text", fail_on=None):
    a = argparse.Namespace()
    a.provider = provider
    a.format = fmt
    a.fail_on = fail_on
    return a


def _empty_report():
    return DriftReport()


def _drift_report():
    r = DriftReport()
    r.entries.append(DriftEntry(
        resource_id="i-1", kind="instance", provider="aws",
        change_type="added", attribute_diff=None
    ))
    return r


def _mock_cfg(providers=("aws",)):
    cfg = MagicMock()
    cfg.providers = [MagicMock(name=p) for p in providers]
    for p in cfg.providers:
        p.name = p.name
    cfg.providers[0].name = providers[0]
    return cfg


def test_cmd_classify_unknown_provider(capsys):
    with patch("driftwatch.commands.classify_cmd.load_config", return_value=_mock_cfg()):
        rc = cmd_classify(_args(provider="gcp"))
    assert rc == 1
    out = capsys.readouterr().out
    assert "Unknown provider" in out


def test_cmd_classify_no_baseline(capsys):
    cfg = _mock_cfg()
    result = CompareResult(ok=False, report=_empty_report())
    with patch("driftwatch.commands.classify_cmd.load_config", return_value=cfg), \
         patch("driftwatch.commands.classify_cmd.get_collector") as gc, \
         patch("driftwatch.commands.classify_cmd.compare_to_baseline", return_value=result):
        gc.return_value.collect.return_value = MagicMock()
        rc = cmd_classify(_args())
    assert rc == 1
    assert "No baseline" in capsys.readouterr().out


def test_cmd_classify_no_drift_returns_0(capsys):
    cfg = _mock_cfg()
    result = CompareResult(ok=True, report=_empty_report())
    with patch("driftwatch.commands.classify_cmd.load_config", return_value=cfg), \
         patch("driftwatch.commands.classify_cmd.get_collector") as gc, \
         patch("driftwatch.commands.classify_cmd.compare_to_baseline", return_value=result):
        gc.return_value.collect.return_value = MagicMock()
        rc = cmd_classify(_args())
    assert rc == 0


def test_cmd_classify_fail_on_high_returns_2(capsys):
    cfg = _mock_cfg()
    result = CompareResult(ok=True, report=_drift_report())
    with patch("driftwatch.commands.classify_cmd.load_config", return_value=cfg), \
         patch("driftwatch.commands.classify_cmd.get_collector") as gc, \
         patch("driftwatch.commands.classify_cmd.compare_to_baseline", return_value=result):
        gc.return_value.collect.return_value = MagicMock()
        rc = cmd_classify(_args(fail_on="high"))
    assert rc == 2


def test_cmd_classify_json_output(capsys):
    cfg = _mock_cfg()
    result = CompareResult(ok=True, report=_drift_report())
    with patch("driftwatch.commands.classify_cmd.load_config", return_value=cfg), \
         patch("driftwatch.commands.classify_cmd.get_collector") as gc, \
         patch("driftwatch.commands.classify_cmd.compare_to_baseline", return_value=result):
        gc.return_value.collect.return_value = MagicMock()
        cmd_classify(_args(fmt="json"))
    import json
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "entries" in data
    assert "counts" in data
