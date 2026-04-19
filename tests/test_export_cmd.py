"""Tests for driftwatch/commands/export_cmd.py."""
from __future__ import annotations

import argparse
import json
from unittest.mock import MagicMock, patch

import pytest

from driftwatch.commands.export_cmd import cmd_export
from driftwatch.differ import DriftReport
from driftwatch.snapshot import ResourceSnapshot, Snapshot


def _args(**kwargs):
    defaults = {
        "provider": "mock",
        "format": "json",
        "output": None,
        "config": "driftwatch.yaml",
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _empty_report() -> DriftReport:
    return DriftReport(added=[], removed=[], changed=[])


def _make_snapshot(provider: str = "mock") -> Snapshot:
    snap = Snapshot(provider=provider)
    snap.add(ResourceSnapshot(id="r1", kind="vm", provider=provider, region="us-east-1", attributes={"state": "running"}))
    return snap


def _mock_cfg(provider: str = "mock"):
    cfg = MagicMock()
    cfg.providers = {provider: MagicMock()}
    return cfg


def test_cmd_export_unknown_provider():
    with patch("driftwatch.commands.export_cmd.config.load", return_value=_mock_cfg()):
        rc = cmd_export(_args(provider="nonexistent"))
    assert rc == 1


def test_cmd_export_no_baseline():
    with (
        patch("driftwatch.commands.export_cmd.config.load", return_value=_mock_cfg()),
        patch("driftwatch.commands.export_cmd.get_collector") as mock_gc,
        patch("driftwatch.commands.export_cmd.baseline.load", return_value=None),
    ):
        mock_gc.return_value.collect.return_value = _make_snapshot()
        rc = cmd_export(_args())
    assert rc == 1


def test_cmd_export_json_stdout(capsys):
    report = _empty_report()
    with (
        patch("driftwatch.commands.export_cmd.config.load", return_value=_mock_cfg()),
        patch("driftwatch.commands.export_cmd.get_collector") as mock_gc,
        patch("driftwatch.commands.export_cmd.baseline.load", return_value=_make_snapshot()),
        patch("driftwatch.commands.export_cmd.diff_compare", return_value=report),
        patch("driftwatch.commands.export_cmd.exporter.export", return_value='{"drift": []}') as mock_exp,
    ):
        mock_gc.return_value.collect.return_value = _make_snapshot()
        rc = cmd_export(_args(format="json"))
    assert rc == 0
    captured = capsys.readouterr()
    assert '{"drift": []}' in captured.out
    mock_exp.assert_called_once_with(report, "json")


def test_cmd_export_csv_to_file(tmp_path):
    out_file = str(tmp_path / "report.csv")
    report = _empty_report()
    csv_content = "provider,kind,resource_id,change_type\n"
    with (
        patch("driftwatch.commands.export_cmd.config.load", return_value=_mock_cfg()),
        patch("driftwatch.commands.export_cmd.get_collector") as mock_gc,
        patch("driftwatch.commands.export_cmd.baseline.load", return_value=_make_snapshot()),
        patch("driftwatch.commands.export_cmd.diff_compare", return_value=report),
        patch("driftwatch.commands.export_cmd.exporter.export", return_value=csv_content),
    ):
        mock_gc.return_value.collect.return_value = _make_snapshot()
        rc = cmd_export(_args(format="csv", output=out_file))
    assert rc == 0
    with open(out_file) as fh:
        assert fh.read() == csv_content
