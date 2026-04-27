"""Additional format/edge-case tests for heatmap_cmd."""
from __future__ import annotations

import argparse
import json
from unittest.mock import patch

from driftwatch.commands.heatmap_cmd import cmd_heatmap
from driftwatch.differ_heatmap import HeatmapReport, HeatmapCell


def _args(**kwargs):
    defaults = {"format": "text", "history_file": None}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _report_one() -> HeatmapReport:
    return HeatmapReport(
        cells=[HeatmapCell("vm-1", "vm", "gcp", drift_count=4, run_count=4)],
        total_runs=4,
    )


def test_json_heat_value_correct(capsys):
    with patch("driftwatch.commands.heatmap_cmd.build_heatmap", return_value=_report_one()):
        cmd_heatmap(_args(format="json"))
    data = json.loads(capsys.readouterr().out)
    assert data["cells"][0]["heat"] == 1.0


def test_text_contains_percentage(capsys):
    with patch("driftwatch.commands.heatmap_cmd.build_heatmap", return_value=_report_one()):
        cmd_heatmap(_args(format="text"))
    out = capsys.readouterr().out
    # heat 1.0 rendered as 100.00%
    assert "%" in out


def test_text_shows_provider(capsys):
    with patch("driftwatch.commands.heatmap_cmd.build_heatmap", return_value=_report_one()):
        cmd_heatmap(_args(format="text"))
    assert "gcp" in capsys.readouterr().out


def test_empty_report_does_not_print_table(capsys):
    empty = HeatmapReport(cells=[], total_runs=0)
    with patch("driftwatch.commands.heatmap_cmd.build_heatmap", return_value=empty):
        cmd_heatmap(_args(format="text"))
    out = capsys.readouterr().out
    assert "RESOURCE" not in out


def test_json_empty_report(capsys):
    empty = HeatmapReport(cells=[], total_runs=0)
    with patch("driftwatch.commands.heatmap_cmd.build_heatmap", return_value=empty):
        rc = cmd_heatmap(_args(format="json"))
    # empty report exits early before json branch
    assert rc == 0
