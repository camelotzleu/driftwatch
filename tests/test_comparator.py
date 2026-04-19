"""Tests for driftwatch.comparator."""
import json
import pathlib
import pytest

from driftwatch.snapshot import Snapshot, ResourceSnapshot
from driftwatch.comparator import compare_to_baseline, compare_snapshots, CompareResult


def _snap(resources=None):
    s = Snapshot(provider="mock", region="us-east-1")
    for r in (resources or []):
        s.add(r)
    return s


def _res(rid, kind="instance", attrs=None):
    return ResourceSnapshot(id=rid, kind=kind, name=rid, region="us-east-1",
                            provider="mock", attributes=attrs or {})


def test_compare_to_baseline_missing(tmp_path):
    result = compare_to_baseline(_snap(), config_dir=str(tmp_path))
    assert result.baseline_missing is True
    assert result.report is None
    assert not result.ok


def test_compare_to_baseline_no_drift(tmp_path):
    snap = _snap([_res("r1", attrs={"state": "running"})])
    # save baseline manually
    from driftwatch.baseline import save
    save(snap, config_dir=str(tmp_path))
    result = compare_to_baseline(snap, config_dir=str(tmp_path))
    assert result.ok
    assert result.report is not None
    assert not result.report.has_drift()


def test_compare_to_baseline_with_drift(tmp_path):
    old = _snap([_res("r1", attrs={"state": "running"})])
    new = _snap([_res("r1", attrs={"state": "stopped"})])
    from driftwatch.baseline import save
    save(old, config_dir=str(tmp_path))
    result = compare_to_baseline(new, config_dir=str(tmp_path))
    assert result.ok
    assert result.report.has_drift()


def test_compare_snapshots_added():
    old = _snap([])
    new = _snap([_res("r1")])
    report = compare_snapshots(old, new)
    assert any(e.change_type == "added" for e in report.entries)


def test_compare_result_ok_flag():
    r = CompareResult(report=None, error="boom")
    assert not r.ok
    r2 = CompareResult(report=None, baseline_missing=True)
    assert not r2.ok
