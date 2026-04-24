"""Tests for driftwatch.differ_flapper."""
from __future__ import annotations

import json
import uuid
from pathlib import Path

import pytest

from driftwatch.differ_flapper import detect_flapping, FlapEntry, FlapReport


def _write_history(tmp_path: Path, entries: list[dict]) -> str:
    p = tmp_path / "history.jsonl"
    with p.open("w") as fh:
        for e in entries:
            fh.write(json.dumps(e) + "\n")
    return str(p)


def _run(run_id: str, resource_id: str, kind: str = "vm", provider: str = "aws") -> dict:
    return {
        "run_id": run_id,
        "drift": {
            "entries": [
                {"resource_id": resource_id, "kind": kind, "provider": provider, "change_type": "changed"}
            ]
        },
    }


# ---------------------------------------------------------------------------


def test_detect_flapping_empty_history(tmp_path):
    p = tmp_path / "empty.jsonl"
    p.write_text("")
    report = detect_flapping(str(p), threshold=2)
    assert isinstance(report, FlapReport)
    assert report.entries == []
    assert report.total_dict()["total"] == 0  # via to_dict


def test_detect_flapping_empty_history_via_to_dict(tmp_path):
    p = tmp_path / "empty.jsonl"
    p.write_text("")
    report = detect_flapping(str(p), threshold=2)
    d = report.to_dict()
    assert d["total"] == 0
    assert d["threshold"] == 2
    assert d["flapping_resources"] == []


def test_detect_flapping_below_threshold(tmp_path):
    history = [_run("run-1", "i-001")]
    path = _write_history(tmp_path, history)
    report = detect_flapping(path, threshold=2)
    assert report.entries == []


def test_detect_flapping_meets_threshold(tmp_path):
    history = [
        _run("run-1", "i-001"),
        _run("run-2", "i-001"),
    ]
    path = _write_history(tmp_path, history)
    report = detect_flapping(path, threshold=2)
    assert len(report.entries) == 1
    entry = report.entries[0]
    assert entry.resource_id == "i-001"
    assert entry.flap_count == 2
    assert set(entry.run_ids) == {"run-1", "run-2"}


def test_detect_flapping_multiple_resources(tmp_path):
    history = [
        _run("run-1", "i-001"),
        _run("run-2", "i-001"),
        _run("run-3", "i-001"),
        _run("run-1", "i-002"),
    ]
    path = _write_history(tmp_path, history)
    report = detect_flapping(path, threshold=2)
    ids = [e.resource_id for e in report.entries]
    assert "i-001" in ids
    assert "i-002" not in ids


def test_detect_flapping_sorted_descending(tmp_path):
    history = [
        _run("run-1", "i-001"),
        _run("run-2", "i-001"),
        _run("run-3", "i-001"),
        _run("run-1", "i-002"),
        _run("run-2", "i-002"),
    ]
    path = _write_history(tmp_path, history)
    report = detect_flapping(path, threshold=2)
    assert report.entries[0].resource_id == "i-001"
    assert report.entries[0].flap_count == 3


def test_flap_entry_to_dict():
    entry = FlapEntry(resource_id="r-1", kind="vm", provider="gcp", flap_count=3, run_ids=["a", "b", "c"])
    d = entry.to_dict()
    assert d["resource_id"] == "r-1"
    assert d["flap_count"] == 3
    assert d["run_ids"] == ["a", "b", "c"]


def test_detect_flapping_deduplicates_same_run(tmp_path):
    # Same run_id appearing twice should only count once.
    history = [
        _run("run-1", "i-001"),
        _run("run-1", "i-001"),  # duplicate
    ]
    path = _write_history(tmp_path, history)
    report = detect_flapping(path, threshold=2)
    assert report.entries == []


# Patch to_dict helper used in empty test
FlapReport.total_dict = FlapReport.to_dict
