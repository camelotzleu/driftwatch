"""Tests for driftwatch.auditor."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from driftwatch.auditor import audit_path, record, load, clear, AuditEntry
from driftwatch.differ import DriftReport, DriftEntry


def _make_entry(kind="changed") -> DriftEntry:
    return DriftEntry(resource_id="r1", kind=kind, provider="aws",
                      resource_type="ec2", before={}, after={}, attribute_diff={})


def _empty_report() -> DriftReport:
    return DriftReport(added=[], removed=[], changed=[])


def _drift_report() -> DriftReport:
    return DriftReport(
        added=[_make_entry("added")],
        removed=[_make_entry("removed")],
        changed=[_make_entry("changed")],
    )


def test_record_creates_file(tmp_path):
    cfg = str(tmp_path)
    record(_empty_report(), "aws", config_dir=cfg)
    assert audit_path(cfg).exists()


def test_record_writes_valid_jsonl(tmp_path):
    cfg = str(tmp_path)
    record(_drift_report(), "gcp", config_dir=cfg)
    lines = audit_path(cfg).read_text().strip().splitlines()
    assert len(lines) == 1
    data = json.loads(lines[0])
    assert data["provider"] == "gcp"
    assert data["added"] == 1
    assert data["removed"] == 1
    assert data["changed"] == 1
    assert data["has_drift"] is True


def test_record_no_drift(tmp_path):
    cfg = str(tmp_path)
    entry = record(_empty_report(), "azure", config_dir=cfg)
    assert entry.has_drift is False
    assert entry.total_resources == 0


def test_record_with_alerts_and_note(tmp_path):
    cfg = str(tmp_path)
    entry = record(_drift_report(), "aws",
                   triggered_alerts=["high-severity"], note="manual run",
                   config_dir=cfg)
    assert entry.triggered_alerts == ["high-severity"]
    assert entry.note == "manual run"


def test_load_returns_entries(tmp_path):
    cfg = str(tmp_path)
    record(_drift_report(), "aws", config_dir=cfg)
    record(_empty_report(), "gcp", config_dir=cfg)
    entries = load(cfg)
    assert len(entries) == 2
    assert entries[0].provider == "aws"
    assert entries[1].provider == "gcp"


def test_load_returns_empty_when_no_file(tmp_path):
    entries = load(str(tmp_path))
    assert entries == []


def test_clear_removes_file(tmp_path):
    cfg = str(tmp_path)
    record(_empty_report(), "aws", config_dir=cfg)
    assert audit_path(cfg).exists()
    clear(cfg)
    assert not audit_path(cfg).exists()


def test_clear_no_file_no_error(tmp_path):
    clear(str(tmp_path))  # should not raise
