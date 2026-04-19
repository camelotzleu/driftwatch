"""Tests for baseline_diff_cmd."""
import argparse
import json
from unittest.mock import patch, MagicMock
import pytest
from driftwatch.commands.baseline_diff_cmd import cmd_baseline_diff
from driftwatch.snapshot import Snapshot, ResourceSnapshot
from driftwatch.snapshot import fingerprint


def _snap_with(rid: str) -> Snapshot:
    s = Snapshot(provider="aws")
    attrs = {"state": "running"}
    s.add(ResourceSnapshot(resource_id=rid, provider="aws", kind="ec2",
                            attributes=attrs, fingerprint=fingerprint(attrs)))
    return s


def _args(old="old.json", new="new.json", fmt="text") -> argparse.Namespace:
    return argparse.Namespace(old=old, new=new, format=fmt)


def test_cmd_missing_old_baseline(capsys):
    with patch("driftwatch.commands.baseline_diff_cmd.load_baseline", return_value=None):
        rc = cmd_baseline_diff(_args())
    assert rc == 1
    captured = capsys.readouterr()
    assert "not found" in captured.err


def test_cmd_missing_new_baseline(capsys):
    old = _snap_with("r1")
    def _load(path):
        return old if path == "old.json" else None
    with patch("driftwatch.commands.baseline_diff_cmd.load_baseline", side_effect=_load):
        rc = cmd_baseline_diff(_args())
    assert rc == 1


def test_cmd_no_changes_text(capsys):
    s = _snap_with("r1")
    with patch("driftwatch.commands.baseline_diff_cmd.load_baseline", return_value=s):
        rc = cmd_baseline_diff(_args())
    assert rc == 0
    out = capsys.readouterr().out
    assert "No changes" in out


def test_cmd_changes_text(capsys):
    old = Snapshot(provider="aws")
    new = _snap_with("r1")
    def _load(path):
        return old if path == "old.json" else new
    with patch("driftwatch.commands.baseline_diff_cmd.load_baseline", side_effect=_load):
        rc = cmd_baseline_diff(_args())
    assert rc == 0
    out = capsys.readouterr().out
    assert "added" in out.lower()


def test_cmd_json_output(capsys):
    old = Snapshot(provider="aws")
    new = _snap_with("r1")
    def _load(path):
        return old if path == "old.json" else new
    with patch("driftwatch.commands.baseline_diff_cmd.load_baseline", side_effect=_load):
        rc = cmd_baseline_diff(_args(fmt="json"))
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert data["has_changes"] is True
    assert data["summary"]["added"] == 1
