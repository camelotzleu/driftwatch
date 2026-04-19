"""Tests for driftwatch.differ_snapshot_diff."""
import pytest
from driftwatch.snapshot import Snapshot, ResourceSnapshot
from driftwatch.differ_snapshot_diff import diff_snapshots, SnapshotDiffResult


def _res(rid: str, attrs: dict) -> ResourceSnapshot:
    return ResourceSnapshot(resource_id=rid, kind="Instance", provider="aws", region="us-east-1", attributes=attrs)


def _snap(*resources: ResourceSnapshot) -> Snapshot:
    s = Snapshot(provider="aws")
    for r in resources:
        s.add(r)
    return s


def test_diff_identical_snapshots_ok():
    r = _res("i-1", {"state": "running"})
    result = diff_snapshots(_snap(r), _snap(r))
    assert result.ok is True
    assert len(result.report.entries) == 0


def test_diff_added_resource():
    r1 = _res("i-1", {"state": "running"})
    r2 = _res("i-2", {"state": "running"})
    result = diff_snapshots(_snap(r1), _snap(r1, r2))
    assert result.ok is False
    ids = [e.resource_id for e in result.report.entries]
    assert "i-2" in ids
    assert any(e.change_type == "added" for e in result.report.entries)


def test_diff_removed_resource():
    r1 = _res("i-1", {"state": "running"})
    r2 = _res("i-2", {"state": "running"})
    result = diff_snapshots(_snap(r1, r2), _snap(r1), old_label="v1", new_label="v2")
    assert result.ok is False
    assert any(e.change_type == "removed" for e in result.report.entries)


def test_diff_changed_attribute():
    old = _res("i-1", {"state": "running"})
    new = _res("i-1", {"state": "stopped"})
    result = diff_snapshots(_snap(old), _snap(new))
    assert result.ok is False
    assert any(e.change_type == "changed" for e in result.report.entries)


def test_to_dict_structure():
    r = _res("i-1", {"state": "running"})
    result = diff_snapshots(_snap(r), _snap(r), old_label="a", new_label="b")
    d = result.to_dict()
    assert d["old_label"] == "a"
    assert d["new_label"] == "b"
    assert d["ok"] is True
    assert d["drift_count"] == 0
    assert isinstance(d["entries"], list)


def test_labels_propagated():
    r = _res("i-1", {})
    result = diff_snapshots(_snap(r), _snap(r), old_label="snap-2024", new_label="snap-2025")
    assert result.old_label == "snap-2024"
    assert result.new_label == "snap-2025"
