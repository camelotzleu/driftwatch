"""Tests for driftwatch.commands.snapshotter_cmd."""
from __future__ import annotations

import argparse
from unittest.mock import MagicMock, patch

import pytest

from driftwatch.commands import snapshotter_cmd as sc
from driftwatch.differ import DriftReport
from driftwatch.snapshot import ResourceSnapshot, Snapshot


def _snap(*rids: str) -> Snapshot:
    s = Snapshot(provider="mock", region="us-east-1")
    for rid in rids:
        s.add(
            ResourceSnapshot(
                resource_id=rid,
                kind="instance",
                provider="mock",
                region="us-east-1",
                attributes={},
            )
        )
    return s


def _args(**kwargs) -> argparse.Namespace:
    defaults = {"config": None, "sub": "list", "provider": "mock", "label": "v1",
                "old": "v1", "new": "v2", "format": "text"}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _fresh_store():
    """Reset module-level store before each test."""
    sc._store = sc.SnapshotStore()


# ---------------------------------------------------------------------------

def test_cmd_list_empty(capsys):
    _fresh_store()
    rc = sc.cmd_snapshotter(_args(sub="list"))
    assert rc == 0
    out = capsys.readouterr().out
    assert "No snapshots" in out


def test_cmd_capture_and_list(capsys):
    _fresh_store()
    snap = _snap("r1")
    with patch("driftwatch.commands.snapshotter_cmd.load_config"), \
         patch("driftwatch.commands.snapshotter_cmd.collect_snapshot", return_value=snap):
        rc = sc.cmd_snapshotter(_args(sub="capture", label="alpha", provider="mock"))
    assert rc == 0
    assert sc._store.get("alpha") is snap


def test_cmd_capture_unknown_provider(capsys):
    _fresh_store()
    with patch("driftwatch.commands.snapshotter_cmd.load_config"), \
         patch("driftwatch.commands.snapshotter_cmd.collect_snapshot", return_value=None):
        rc = sc.cmd_snapshotter(_args(sub="capture", label="x", provider="unknown"))
    assert rc == 1


def test_cmd_compare_no_drift(capsys):
    _fresh_store()
    snap = _snap("r1")
    sc._store.put("v1", snap)
    sc._store.put("v2", snap)
    with patch("driftwatch.commands.snapshotter_cmd.load_config"):
        rc = sc.cmd_snapshotter(_args(sub="compare", old="v1", new="v2", format="text"))
    assert rc == 0


def test_cmd_compare_missing_label(capsys):
    _fresh_store()
    sc._store.put("v1", _snap("r1"))
    with patch("driftwatch.commands.snapshotter_cmd.load_config"):
        rc = sc.cmd_snapshotter(_args(sub="compare", old="v1", new="missing", format="text"))
    assert rc == 1


def test_cmd_drop_existing(capsys):
    _fresh_store()
    sc._store.put("old", _snap())
    with patch("driftwatch.commands.snapshotter_cmd.load_config"):
        rc = sc.cmd_snapshotter(_args(sub="drop", label="old"))
    assert rc == 0
    assert sc._store.get("old") is None


def test_cmd_drop_missing(capsys):
    _fresh_store()
    with patch("driftwatch.commands.snapshotter_cmd.load_config"):
        rc = sc.cmd_snapshotter(_args(sub="drop", label="ghost"))
    assert rc == 1


def test_register_adds_subparser():
    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers(dest="cmd")
    sc.register(subs)
    args = parser.parse_args(["snapshotter", "list"])
    assert args.sub == "list"
