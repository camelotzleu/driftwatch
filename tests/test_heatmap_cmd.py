"""Tests for driftwatch.commands.heatmap_cmd."""
from __future__ import annotations

import argparse
import json
from unittest.mock import patch, MagicMock

import pytest

from driftwatch.commands.heatmap_cmd import cmd_heatmap, register
from driftwatch.differ_heatmap import HeatmapReport, HeatmapCell


def _args(**kwargs) -> argparse.Namespace:
    defaults = {"format": "text", "history_file": None}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _empty_report() -> HeatmapReport:
    return HeatmapReport(cells=[], total_runs=0)


def _populated_report() -> HeatmapReport:
    return HeatmapReport(
        cells=[
            HeatmapCell(resource_id="i-001", kind="instance", provider="aws", drift_count=3, run_count=5),
            HeatmapCell(resource_id="i-002", kind="instance", provider="aws", drift_count=1, run_count=5),
        ],
        total_runs=5,
    )


# ---------------------------------------------------------------------------

def test_cmd_heatmap_empty_returns_0(capsys):
    with patch("driftwatch.commands.heatmap_cmd.build_heatmap", return_value=_empty_report()):
        rc = cmd_heatmap(_args())
    assert rc == 0
    captured = capsys.readouterr()
    assert "empty" in captured.out.lower()


def test_cmd_heatmap_text_output(capsys):
    with patch("driftwatch.commands.heatmap_cmd.build_heatmap", return_value=_populated_report()):
        rc = cmd_heatmap(_args(format="text"))
    assert rc == 0
    out = capsys.readouterr().out
    assert "i-001" in out
    assert "i-002" in out
    assert "Total runs" in out


def test_cmd_heatmap_json_output(capsys):
    with patch("driftwatch.commands.heatmap_cmd.build_heatmap", return_value=_populated_report()):
        rc = cmd_heatmap(_args(format="json"))
    assert rc == 0
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "cells" in data
    assert data["total_runs"] == 5
    assert len(data["cells"]) == 2


def test_cmd_heatmap_passes_history_file():
    with patch("driftwatch.commands.heatmap_cmd.build_heatmap", return_value=_empty_report()) as mock_build:
        cmd_heatmap(_args(history_file="/tmp/custom.jsonl"))
    mock_build.assert_called_once_with("/tmp/custom.jsonl")


def test_register_adds_heatmap_subparser():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    register(sub)
    args = parser.parse_args(["heatmap"])
    assert hasattr(args, "func")
