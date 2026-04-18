"""Tests for driftwatch.baseline module."""

import json
from pathlib import Path

import pytest

from driftwatch.baseline import save, load, exists, baseline_path
from driftwatch.snapshot import Snapshot, ResourceSnapshot


def _make_snapshot() -> Snapshot:
    s = Snapshot()
    s.add(ResourceSnapshot(provider="aws", resource_type="s3", resource_id="my-bucket", attributes={"versioning": True}))
    s.add(ResourceSnapshot(provider="aws", resource_type="ec2", resource_id="i-123", attributes={"instance_type": "t3.micro"}))
    return s


def test_save_creates_file(tmp_path):
    snap = _make_snapshot()
    target = tmp_path / "baseline.json"
    result = save(snap, path=target)
    assert result == target
    assert target.exists()


def test_save_valid_json(tmp_path):
    snap = _make_snapshot()
    target = tmp_path / "baseline.json"
    save(snap, path=target)
    data = json.loads(target.read_text())
    assert "resources" in data
    assert len(data["resources"]) == 2


def test_load_returns_snapshot(tmp_path):
    snap = _make_snapshot()
    target = tmp_path / "baseline.json"
    save(snap, path=target)
    loaded = load(path=target)
    assert loaded is not None
    assert len(loaded.resources) == 2


def test_load_returns_none_when_missing(tmp_path):
    target = tmp_path / "nonexistent.json"
    assert load(path=target) is None


def test_exists_true(tmp_path):
    snap = _make_snapshot()
    target = tmp_path / "baseline.json"
    save(snap, path=target)
    assert exists(path=target) is True


def test_exists_false(tmp_path):
    assert exists(path=tmp_path / "missing.json") is False


def test_roundtrip_preserves_attributes(tmp_path):
    snap = _make_snapshot()
    target = tmp_path / "baseline.json"
    save(snap, path=target)
    loaded = load(path=target)
    original_ids = {r.resource_id for r in snap.resources}
    loaded_ids = {r.resource_id for r in loaded.resources}
    assert original_ids == loaded_ids


def test_baseline_path_default():
    p = baseline_path()
    assert p == Path(".driftwatch") / "baseline.json"
