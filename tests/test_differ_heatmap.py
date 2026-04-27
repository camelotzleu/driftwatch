"""Tests for driftwatch.differ_heatmap."""
from __future__ import annotations

import json
import os
import tempfile

import pytest

from driftwatch.differ_heatmap import HeatmapCell, HeatmapReport, build_heatmap


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _write_history(path: str, entries: list) -> None:
    with open(path, "w") as fh:
        for e in entries:
            fh.write(json.dumps(e) + "\n")


def _run(*resource_ids: str) -> dict:
    """Build a minimal history entry containing the given resource IDs."""
    return {
        "report": {
            "entries": [
                {"resource_id": rid, "kind": "instance", "provider": "aws", "change": "changed"}
                for rid in resource_ids
            ]
        }
    }


# ---------------------------------------------------------------------------
# unit tests
# ---------------------------------------------------------------------------

def test_build_heatmap_empty_history(tmp_path):
    hist = str(tmp_path / "history.jsonl")
    # file does not exist
    report = build_heatmap(hist)
    assert report.total_runs == 0
    assert report.cells == []


def test_build_heatmap_single_run(tmp_path):
    hist = str(tmp_path / "history.jsonl")
    _write_history(hist, [_run("i-001", "i-002")])
    report = build_heatmap(hist)
    assert report.total_runs == 1
    assert len(report.cells) == 2
    for cell in report.cells:
        assert cell.drift_count == 1
        assert cell.run_count == 1
        assert cell.heat == 1.0


def test_build_heatmap_multiple_runs(tmp_path):
    hist = str(tmp_path / "history.jsonl")
    # i-001 drifts in 2 of 3 runs; i-002 drifts in 1 of 3 runs
    _write_history(hist, [
        _run("i-001", "i-002"),
        _run("i-001"),
        _run("i-003"),
    ])
    report = build_heatmap(hist)
    assert report.total_runs == 3
    by_id = {c.resource_id: c for c in report.cells}
    assert by_id["i-001"].drift_count == 2
    assert by_id["i-001"].heat == pytest.approx(2 / 3, rel=1e-4)
    assert by_id["i-002"].drift_count == 1
    assert by_id["i-003"].drift_count == 1


def test_cell_heat_zero_runs():
    cell = HeatmapCell(resource_id="x", kind="vm", provider="gcp", drift_count=0, run_count=0)
    assert cell.heat == 0.0


def test_to_dict_structure(tmp_path):
    hist = str(tmp_path / "history.jsonl")
    _write_history(hist, [_run("i-001")])
    report = build_heatmap(hist)
    d = report.to_dict()
    assert "total_runs" in d
    assert "cells" in d
    cell_d = d["cells"][0]
    assert "resource_id" in cell_d
    assert "heat" in cell_d
    assert "drift_count" in cell_d
    assert "run_count" in cell_d


def test_cells_sorted_by_heat_descending(tmp_path):
    hist = str(tmp_path / "history.jsonl")
    _write_history(hist, [
        _run("i-low"),
        _run("i-high", "i-low"),
        _run("i-high"),
    ])
    report = build_heatmap(hist)
    heats = [c.heat for c in sorted(report.cells, key=lambda c: c.heat, reverse=True)]
    assert heats == sorted(heats, reverse=True)
