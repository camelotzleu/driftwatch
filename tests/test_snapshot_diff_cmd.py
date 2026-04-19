"""Tests for driftwatch.commands.snapshot_diff_cmd."""
import json
import argparse
from unittest.mock import patch, MagicMock
from driftwatch.commands.snapshot_diff_cmd import cmd_snapshot_diff
from driftwatch.snapshot import Snapshot, ResourceSnapshot
from driftwatch.differ import DriftReport
from driftwatch.differ_snapshot_diff import SnapshotDiffResult


def _snap() -> Snapshot:
    s = Snapshot(provider="aws")
    s.add(ResourceSnapshot(resource_id="i-1", kind="Instance", provider="aws", region="us-east-1", attributes={}))
    return s


def _args(**kwargs):
    base = {"old": "old.json", "new": "new.json", "format": "text"}
    base.update(kwargs)
    return argparse.Namespace(**base)


def test_cmd_missing_old_baseline(capsys):
    with patch("driftwatch.commands.snapshot_diff_cmd.bl.load", return_value=None):
        rc = cmd_snapshot_diff(_args())
    assert rc == 1


def test_cmd_missing_new_baseline(capsys):
    snap = _snap()
    def _load(path):
        return snap if path == "old.json" else None
    with patch("driftwatch.commands.snapshot_diff_cmd.bl.load", side_effect=_load):
        rc = cmd_snapshot_diff(_args())
    assert rc == 1


def test_cmd_no_drift_returns_0(capsys):
    snap = _snap()
    with patch("driftwatch.commands.snapshot_diff_cmd.bl.load", return_value=snap):
        rc = cmd_snapshot_diff(_args())
    assert rc == 0


def test_cmd_drift_returns_2(capsys):
    old = _snap()
    new = Snapshot(provider="aws")  # empty — resource removed
    def _load(path):
        return old if path == "old.json" else new
    with patch("driftwatch.commands.snapshot_diff_cmd.bl.load", side_effect=_load):
        rc = cmd_snapshot_diff(_args())
    assert rc == 2


def test_cmd_json_format(capsys):
    snap = _snap()
    with patch("driftwatch.commands.snapshot_diff_cmd.bl.load", return_value=snap):
        rc = cmd_snapshot_diff(_args(format="json"))
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "entries" in data
    assert "ok" in data
