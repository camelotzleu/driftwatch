"""Tests for driftwatch.commands.watchlist_cmd."""
from __future__ import annotations

import argparse
from unittest.mock import MagicMock, patch

import pytest

from driftwatch.commands.watchlist_cmd import cmd_watchlist
from driftwatch.comparator import CompareResult
from driftwatch.config import DriftWatchConfig, ProviderConfig
from driftwatch.differ import DriftEntry, DriftReport
from driftwatch.snapshot import Snapshot


def _args(provider="aws", fmt="text"):
    a = argparse.Namespace()
    a.provider = provider
    a.format = fmt
    return a


def _make_cfg(watchlist=None):
    cfg = MagicMock(spec=DriftWatchConfig)
    cfg.providers = [ProviderConfig(name="aws", region="us-east-1")]
    cfg.watchlist = watchlist or []
    return cfg


def _empty_report():
    return DriftReport()


def _drift_report(resource_id="i-123"):
    r = DriftReport()
    r.entries.append(
        DriftEntry(
            resource_id=resource_id,
            kind="Instance",
            provider="aws",
            change_type="changed",
            attribute_diff={},
        )
    )
    return r


# ---------------------------------------------------------------------------


def test_cmd_watchlist_unknown_provider():
    cfg = _make_cfg()
    rc = cmd_watchlist(_args(provider="gcp"), cfg)
    assert rc == 1


def test_cmd_watchlist_no_watchlist_entries():
    cfg = _make_cfg(watchlist=[])
    rc = cmd_watchlist(_args(), cfg)
    assert rc == 1


def test_cmd_watchlist_no_baseline(capsys):
    cfg = _make_cfg(watchlist=[{"resource_id": "i-1"}])
    snap = MagicMock(spec=Snapshot)
    no_baseline = CompareResult(ok=False, report=None)

    with patch("driftwatch.commands.watchlist_cmd.get_collector") as gc, \
         patch("driftwatch.commands.watchlist_cmd.compare_to_baseline",
               return_value=no_baseline):
        gc.return_value.collect.return_value = snap
        rc = cmd_watchlist(_args(), cfg)

    assert rc == 1
    captured = capsys.readouterr()
    assert "no baseline" in captured.err


def test_cmd_watchlist_no_hits(capsys):
    cfg = _make_cfg(watchlist=[{"resource_id": "i-999"}])
    snap = MagicMock(spec=Snapshot)
    result = CompareResult(ok=True, report=_drift_report("i-123"))

    with patch("driftwatch.commands.watchlist_cmd.get_collector") as gc, \
         patch("driftwatch.commands.watchlist_cmd.compare_to_baseline",
               return_value=result):
        gc.return_value.collect.return_value = snap
        rc = cmd_watchlist(_args(), cfg)

    assert rc == 0
    assert "No watched" in capsys.readouterr().out


def test_cmd_watchlist_hit_returns_2(capsys):
    cfg = _make_cfg(watchlist=[{"resource_id": "i-123", "reason": "prod"}])
    snap = MagicMock(spec=Snapshot)
    result = CompareResult(ok=True, report=_drift_report("i-123"))

    with patch("driftwatch.commands.watchlist_cmd.get_collector") as gc, \
         patch("driftwatch.commands.watchlist_cmd.compare_to_baseline",
               return_value=result):
        gc.return_value.collect.return_value = snap
        rc = cmd_watchlist(_args(), cfg)

    assert rc == 2
    out = capsys.readouterr().out
    assert "i-123" in out
    assert "prod" in out


def test_cmd_watchlist_json_output(capsys):
    import json
    cfg = _make_cfg(watchlist=[{"resource_id": "i-123"}])
    snap = MagicMock(spec=Snapshot)
    result = CompareResult(ok=True, report=_drift_report("i-123"))

    with patch("driftwatch.commands.watchlist_cmd.get_collector") as gc, \
         patch("driftwatch.commands.watchlist_cmd.compare_to_baseline",
               return_value=result):
        gc.return_value.collect.return_value = snap
        rc = cmd_watchlist(_args(fmt="json"), cfg)

    assert rc == 2
    data = json.loads(capsys.readouterr().out)
    assert "entries" in data
    assert data["watched_hits"] == 1
