"""Tests for driftwatch.pruner."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone, timedelta

import pytest

from driftwatch.pruner import (
    prune_history_by_age,
    prune_history_by_count,
    prune_baseline_if_stale,
)


def _write_history(path: str, entries: list[dict]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        for e in entries:
            fh.write(json.dumps(e) + "\n")


def _history_path(tmp_path) -> str:
    return str(tmp_path / ".driftwatch" / "history.jsonl")


def _baseline_path(tmp_path) -> str:
    return str(tmp_path / ".driftwatch" / "baseline.json")


def test_prune_history_by_age_removes_old(tmp_path):
    now = datetime.now(timezone.utc)
    old_ts = (now - timedelta(days=10)).isoformat()
    new_ts = now.isoformat()
    hp = _history_path(tmp_path)
    _write_history(hp, [{"timestamp": old_ts, "x": 1}, {"timestamp": new_ts, "x": 2}])
    removed = prune_history_by_age(5, str(tmp_path))
    assert removed == 1
    with open(hp) as fh:
        lines = fh.readlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["x"] == 2


def test_prune_history_by_age_no_file(tmp_path):
    assert prune_history_by_age(5, str(tmp_path)) == 0


def test_prune_history_by_count_keeps_recent(tmp_path):
    hp = _history_path(tmp_path)
    entries = [{"i": i} for i in range(10)]
    _write_history(hp, entries)
    removed = prune_history_by_count(3, str(tmp_path))
    assert removed == 7
    with open(hp) as fh:
        lines = fh.readlines()
    assert len(lines) == 3
    assert json.loads(lines[-1])["i"] == 9


def test_prune_history_by_count_no_op_when_within_limit(tmp_path):
    hp = _history_path(tmp_path)
    _write_history(hp, [{"i": i} for i in range(3)])
    assert prune_history_by_count(5, str(tmp_path)) == 0


def test_prune_baseline_if_stale_removes(tmp_path):
    bp = _baseline_path(tmp_path)
    os.makedirs(os.path.dirname(bp), exist_ok=True)
    with open(bp, "w") as fh:
        json.dump({}, fh)
    old_time = (datetime.now(timezone.utc) - timedelta(days=20)).timestamp()
    os.utime(bp, (old_time, old_time))
    result = prune_baseline_if_stale(10, str(tmp_path))
    assert result is True
    assert not os.path.exists(bp)


def test_prune_baseline_if_stale_keeps_fresh(tmp_path):
    bp = _baseline_path(tmp_path)
    os.makedirs(os.path.dirname(bp), exist_ok=True)
    with open(bp, "w") as fh:
        json.dump({}, fh)
    result = prune_baseline_if_stale(30, str(tmp_path))
    assert result is False
    assert os.path.exists(bp)


def test_prune_baseline_no_file(tmp_path):
    assert prune_baseline_if_stale(7, str(tmp_path)) is False
