"""Tests for driftwatch.differ_scorer."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from driftwatch.differ_scorer import score_by_frequency, FrequencyReport


def _history_entry(resource_id: str, kind: str, provider: str) -> dict:
    return {
        "timestamp": "2024-01-01T00:00:00",
        "report": {
            "entries": [
                {"resource_id": resource_id, "kind": kind, "provider": provider, "change_type": "changed"}
            ]
        },
    }


def test_score_empty_history():
    with patch("driftwatch.differ_scorer.load_history", return_value=[]):
        report = score_by_frequency()
    assert isinstance(report, FrequencyReport)
    assert report.total_runs == 0
    assert report.scores == []


def test_score_single_entry():
    history = [_history_entry("res-1", "EC2Instance", "aws")]
    with patch("driftwatch.differ_scorer.load_history", return_value=history):
        report = score_by_frequency()
    assert report.total_runs == 1
    assert len(report.scores) == 1
    s = report.scores[0]
    assert s.resource_id == "res-1"
    assert s.drift_count == 1
    assert s.change_rate == pytest.approx(1.0)


def test_score_multiple_runs_same_resource():
    history = [
        _history_entry("res-1", "EC2Instance", "aws"),
        _history_entry("res-1", "EC2Instance", "aws"),
        _history_entry("res-2", "Bucket", "aws"),
    ]
    with patch("driftwatch.differ_scorer.load_history", return_value=history):
        report = score_by_frequency()
    assert report.total_runs == 3
    assert report.scores[0].resource_id == "res-1"
    assert report.scores[0].drift_count == 2
    assert report.scores[0].change_rate == pytest.approx(2 / 3)
    assert report.scores[1].resource_id == "res-2"


def test_to_dict_structure():
    history = [_history_entry("r", "VM", "gcp")]
    with patch("driftwatch.differ_scorer.load_history", return_value=history):
        d = score_by_frequency().to_dict()
    assert "total_runs" in d
    assert "scores" in d
    assert d["scores"][0]["resource_id"] == "r"
    assert "change_rate" in d["scores"][0]


def test_scores_sorted_descending():
    history = [
        _history_entry("low", "VM", "gcp"),
        _history_entry("high", "VM", "gcp"),
        _history_entry("high", "VM", "gcp"),
    ]
    with patch("driftwatch.differ_scorer.load_history", return_value=history):
        report = score_by_frequency()
    assert report.scores[0].resource_id == "high"
