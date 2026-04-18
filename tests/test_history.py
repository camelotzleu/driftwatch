"""Tests for driftwatch.history."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from driftwatch.differ import DriftEntry, DriftReport
import driftwatch.history as history_mod


def _make_entry(rid="r-1", provider="aws", kind="ec2"):
    return DriftEntry(
        resource_id=rid,
        provider=provider,
        kind=kind,
        attribute_diff={"instance_type": {"baseline": "t2.micro", "current": "t3.micro"}},
    )


def _make_report(changed=1, added=0, removed=0):
    return DriftReport(
        changed=[_make_entry(rid=f"c-{i}") for i in range(changed)],
        added=[_make_entry(rid=f"a-{i}") for i in range(added)],
        removed=[_make_entry(rid=f"r-{i}") for i in range(removed)],
    )


def test_append_creates_file(tmp_path):
    p = tmp_path / "history.jsonl"
    history_mod.append(_make_report(), path=p)
    assert p.exists()


def test_append_writes_valid_jsonl(tmp_path):
    p = tmp_path / "history.jsonl"
    history_mod.append(_make_report(changed=2), path=p)
    lines = p.read_text().splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["has_drift"] is True
    assert len(entry["changed"]) == 2


def test_append_multiple_entries(tmp_path):
    p = tmp_path / "history.jsonl"
    history_mod.append(_make_report(changed=1), path=p)
    history_mod.append(_make_report(changed=0), path=p)
    entries = history_mod.load(path=p)
    assert len(entries) == 2


def test_load_returns_newest_first(tmp_path):
    p = tmp_path / "history.jsonl"
    history_mod.append(_make_report(changed=1), path=p)
    history_mod.append(_make_report(changed=0), path=p)
    entries = history_mod.load(path=p)
    # newest (no drift) should be first
    assert entries[0]["has_drift"] is False


def test_load_respects_limit(tmp_path):
    p = tmp_path / "history.jsonl"
    for _ in range(10):
        history_mod.append(_make_report(), path=p)
    entries = history_mod.load(path=p, limit=3)
    assert len(entries) == 3


def test_load_returns_empty_when_missing(tmp_path):
    p = tmp_path / "no_such_file.jsonl"
    assert history_mod.load(path=p) == []


def test_clear_removes_file(tmp_path):
    p = tmp_path / "history.jsonl"
    history_mod.append(_make_report(), path=p)
    history_mod.clear(path=p)
    assert not p.exists()


def test_clear_noop_when_missing(tmp_path):
    p = tmp_path / "ghost.jsonl"
    history_mod.clear(path=p)  # should not raise


def test_entry_fields_persisted(tmp_path):
    p = tmp_path / "history.jsonl"
    history_mod.append(_make_report(changed=1), path=p)
    entry = history_mod.load(path=p)[0]
    c = entry["changed"][0]
    assert c["resource_id"] == "c-0"
    assert c["provider"] == "aws"
    assert "instance_type" in c["attribute_diff"]
