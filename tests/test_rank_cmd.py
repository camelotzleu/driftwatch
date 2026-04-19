"""Tests for driftwatch.commands.rank_cmd."""
import argparse
from unittest.mock import MagicMock, patch
from driftwatch.differ import DriftReport, DriftEntry
from driftwatch.commands.rank_cmd import cmd_rank


def _args(**kwargs):
    defaults = {"provider": "aws", "format": "text", "top": 0}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _empty_report():
    return DriftReport()


def _drift_report():
    r = DriftReport()
    r.entries.append(DriftEntry(
        resource_id="i-123", kind="instance", provider="aws",
        change_type="added", attribute_diff={},
    ))
    return r


def _mock_cfg(provider="aws"):
    pcfg = MagicMock()
    pcfg.name = provider
    cfg = MagicMock()
    cfg.providers = [pcfg]
    return cfg


def test_cmd_rank_unknown_provider(capsys):
    with patch("driftwatch.commands.rank_cmd.load_config", return_value=_mock_cfg()):
        result = cmd_rank(_args(provider="gcp"))
    assert result == 1
    out = capsys.readouterr().out
    assert "Unknown provider" in out


def test_cmd_rank_no_baseline(capsys):
    with patch("driftwatch.commands.rank_cmd.load_config", return_value=_mock_cfg()), \
         patch("driftwatch.commands.rank_cmd.load_baseline", return_value=None):
        result = cmd_rank(_args())
    assert result == 1
    assert "No baseline" in capsys.readouterr().out


def test_cmd_rank_no_drift(capsys):
    snap = MagicMock()
    collector = MagicMock()
    collector.collect.return_value = snap
    with patch("driftwatch.commands.rank_cmd.load_config", return_value=_mock_cfg()), \
         patch("driftwatch.commands.rank_cmd.load_baseline", return_value=snap), \
         patch("driftwatch.commands.rank_cmd.get_collector", return_value=collector), \
         patch("driftwatch.commands.rank_cmd.diff", return_value=_empty_report()):
        result = cmd_rank(_args())
    assert result == 0
    assert "No drift" in capsys.readouterr().out


def test_cmd_rank_with_drift_text(capsys):
    snap = MagicMock()
    collector = MagicMock()
    collector.collect.return_value = snap
    with patch("driftwatch.commands.rank_cmd.load_config", return_value=_mock_cfg()), \
         patch("driftwatch.commands.rank_cmd.load_baseline", return_value=snap), \
         patch("driftwatch.commands.rank_cmd.get_collector", return_value=collector), \
         patch("driftwatch.commands.rank_cmd.diff", return_value=_drift_report()):
        result = cmd_rank(_args())
    assert result == 0
    out = capsys.readouterr().out
    assert "i-123" in out


def test_cmd_rank_json_format(capsys):
    import json
    snap = MagicMock()
    collector = MagicMock()
    collector.collect.return_value = snap
    with patch("driftwatch.commands.rank_cmd.load_config", return_value=_mock_cfg()), \
         patch("driftwatch.commands.rank_cmd.load_baseline", return_value=snap), \
         patch("driftwatch.commands.rank_cmd.get_collector", return_value=collector), \
         patch("driftwatch.commands.rank_cmd.diff", return_value=_drift_report()):
        result = cmd_rank(_args(format="json"))
    assert result == 0
    data = json.loads(capsys.readouterr().out)
    assert "ranked" in data
