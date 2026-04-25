"""Integration-style tests for throttle rule loading in cmd."""
from __future__ import annotations

import argparse
from unittest.mock import MagicMock, patch

from driftwatch.commands.throttle_cmd import _rules_from_config, cmd_throttle
from driftwatch.comparator import CompareResult
from driftwatch.differ import DriftEntry, DriftReport


def _make_cfg(rules=None):
    cfg = MagicMock()
    cfg.throttle_rules = rules or []
    return cfg


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


# ---------------------------------------------------------------------------
# _rules_from_config
# ---------------------------------------------------------------------------

def test_rules_from_config_empty():
    rules = _rules_from_config(_make_cfg([]))
    assert rules == []


def test_rules_from_config_single():
    raw = [{"kind": "instance", "cooldown_seconds": "120"}]
    rules = _rules_from_config(_make_cfg(raw))
    assert len(rules) == 1
    assert rules[0].kind == "instance"
    assert rules[0].cooldown_seconds == 120


def test_rules_from_config_defaults():
    raw = [{"provider": "aws"}]
    rules = _rules_from_config(_make_cfg(raw))
    assert rules[0].cooldown_seconds == 3600
    assert rules[0].kind is None
    assert rules[0].resource_id is None


# ---------------------------------------------------------------------------
# cmd_throttle with a matching rule suppresses repeated entry
# ---------------------------------------------------------------------------

def test_cmd_throttle_suppresses_with_rule(tmp_path, capsys, monkeypatch):
    monkeypatch.chdir(tmp_path)
    raw_rules = [{"kind": "instance", "cooldown_seconds": "3600"}]
    cfg = _make_cfg(raw_rules)

    mock_collector = MagicMock()
    mock_collector.collect.return_value = MagicMock()
    ok_result = CompareResult(ok=True, report=_drift_report())

    args = argparse.Namespace(provider="mock", format="text")

    with patch("driftwatch.commands.throttle_cmd.get_collector", return_value=mock_collector), \
         patch("driftwatch.commands.throttle_cmd.compare_to_baseline", return_value=ok_result):
        # First call — allowed
        rc1 = cmd_throttle(args, cfg)
        out1 = capsys.readouterr().out
        assert rc1 == 0
        assert "Allowed  : 1" in out1

        # Second call — suppressed (same cooldown window)
        rc2 = cmd_throttle(args, cfg)
        out2 = capsys.readouterr().out
        assert rc2 == 0
        assert "Suppressed: 1" in out2
