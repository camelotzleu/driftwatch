"""Tests for driftwatch.differ_snapshotter."""
from __future__ import annotations

import pytest

from driftwatch.differ_snapshotter import (
    LabeledSnapshot,
    SnapshotCompareResult,
    SnapshotStore,
    compare_labeled,
)
from driftwatch.snapshot import ResourceSnapshot, Snapshot


def _snap(*resources: ResourceSnapshot) -> Snapshot:
    s = Snapshot(provider="mock", region="us-east-1")
    for r in resources:
        s.add(r)
    return s


def _res(rid: str, kind: str = "instance", **attrs) -> ResourceSnapshot:
    return ResourceSnapshot(
        resource_id=rid,
        kind=kind,
        provider="mock",
        region="us-east-1",
        attributes=attrs,
    )


# ---------------------------------------------------------------------------
# SnapshotStore
# ---------------------------------------------------------------------------

def test_store_put_and_get():
    store = SnapshotStore()
    snap = _snap(_res("r1"))
    store.put("alpha", snap)
    assert store.get("alpha") is snap


def test_store_get_missing_returns_none():
    store = SnapshotStore()
    assert store.get("nope") is None


def test_store_labels():
    store = SnapshotStore()
    store.put("a", _snap())
    store.put("b", _snap())
    assert set(store.labels()) == {"a", "b"}


def test_store_remove_existing():
    store = SnapshotStore()
    store.put("x", _snap())
    assert store.remove("x") is True
    assert store.get("x") is None


def test_store_remove_missing():
    store = SnapshotStore()
    assert store.remove("ghost") is False


# ---------------------------------------------------------------------------
# compare_labeled
# ---------------------------------------------------------------------------

def test_compare_labeled_no_drift():
    store = SnapshotStore()
    r = _res("r1", state="running")
    store.put("v1", _snap(r))
    store.put("v2", _snap(r))
    result = compare_labeled(store, "v1", "v2")
    assert result.ok is True
    assert not result.report.has_drift()


def test_compare_labeled_detects_drift():
    store = SnapshotStore()
    store.put("v1", _snap(_res("r1", state="running")))
    store.put("v2", _snap(_res("r1", state="stopped")))
    result = compare_labeled(store, "v1", "v2")
    assert result.ok is False
    assert result.report.has_drift()


def test_compare_labeled_missing_old_raises():
    store = SnapshotStore()
    store.put("v2", _snap())
    with pytest.raises(KeyError, match="v1"):
        compare_labeled(store, "v1", "v2")


def test_compare_labeled_missing_new_raises():
    store = SnapshotStore()
    store.put("v1", _snap())
    with pytest.raises(KeyError, match="v2"):
        compare_labeled(store, "v1", "v2")


def test_compare_result_to_dict():
    store = SnapshotStore()
    store.put("old", _snap(_res("r1", state="running")))
    store.put("new", _snap(_res("r1", state="stopped")))
    result = compare_labeled(store, "old", "new")
    d = result.to_dict()
    assert d["old_label"] == "old"
    assert d["new_label"] == "new"
    assert "has_drift" in d
    assert "entries" in d
    assert isinstance(d["entries"], list)
