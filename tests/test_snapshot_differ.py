"""Tests for snapshot capture and drift comparison."""

import json
from pathlib import Path

import pytest

from driftwatch.snapshot import ResourceSnapshot, Snapshot
from driftwatch.differ import compare, DriftReport


def make_resource(rid: str, attrs: dict) -> ResourceSnapshot:
    return ResourceSnapshot(
        provider="aws",
        resource_type="s3_bucket",
        resource_id=rid,
        attributes=attrs,
    )


def test_resource_fingerprint_changes_with_attributes():
    r1 = make_resource("bucket-1", {"versioning": True})
    r2 = make_resource("bucket-1", {"versioning": False})
    assert r1.fingerprint != r2.fingerprint


def test_resource_fingerprint_stable():
    r = make_resource("bucket-1", {"region": "us-east-1"})
    assert r.fingerprint == r.fingerprint


def test_snapshot_add_and_to_dict():
    snap = Snapshot(label="baseline")
    snap.add(make_resource("b1", {"acl": "private"}))
    d = snap.to_dict()
    assert d["label"] == "baseline"
    assert len(d["resources"]) == 1


def test_snapshot_roundtrip(tmp_path: Path):
    snap = Snapshot(label="test")
    snap.add(make_resource("b1", {"acl": "public"}))
    out = tmp_path / "snap.json"
    snap.save(out)
    loaded = Snapshot.load(out)
    assert loaded.label == "test"
    assert loaded.resources[0].resource_id == "b1"


def test_no_drift_identical_snapshots():
    r = make_resource("b1", {"acl": "private"})
    baseline = Snapshot(label="baseline")
    baseline.add(r)
    current = Snapshot(label="current")
    current.add(make_resource("b1", {"acl": "private"}))
    report = compare(baseline, current)
    assert not report.has_drift


def test_drift_detected_on_change():
    baseline = Snapshot(label="baseline")
    baseline.add(make_resource("b1", {"acl": "private"}))
    current = Snapshot(label="current")
    current.add(make_resource("b1", {"acl": "public"}))
    report = compare(baseline, current)
    assert report.has_drift
    assert report.entries[0].status == "changed"
    assert "acl" in report.entries[0].diff


def test_drift_detected_on_removal():
    baseline = Snapshot(label="baseline")
    baseline.add(make_resource("b1", {}))
    current = Snapshot(label="current")
    report = compare(baseline, current)
    assert any(e.status == "removed" for e in report.entries)


def test_drift_detected_on_addition():
    baseline = Snapshot(label="baseline")
    current = Snapshot(label="current")
    current.add(make_resource("b2", {}))
    report = compare(baseline, current)
    assert any(e.status == "added" for e in report.entries)


def test_summary_no_drift():
    report = DriftReport("a", "b", [])
    assert "No drift" in report.summary()
