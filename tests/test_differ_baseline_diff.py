"""Tests for differ_baseline_diff."""
import pytest
from driftwatch.snapshot import Snapshot, ResourceSnapshot
from driftwatch.differ_baseline_diff import diff_baselines, BaselineDiffReport


def _res(rid: str, provider: str = "aws", kind: str = "ec2", attrs: dict | None = None) -> ResourceSnapshot:
    from driftwatch.snapshot import fingerprint
    a = attrs or {"state": "running"}
    return ResourceSnapshot(
        resource_id=rid, provider=provider, kind=kind,
        attributes=a, fingerprint=fingerprint(a),
    )


def _snap(*resources: ResourceSnapshot) -> Snapshot:
    s = Snapshot(provider="aws")
    for r in resources:
        s.add(r)
    return s


def test_diff_empty_snapshots():
    report = diff_baselines(_snap(), _snap())
    assert not report.has_changes
    assert report.summary() == {"added": 0, "removed": 0, "changed": 0}


def test_diff_added_resource():
    old = _snap()
    new = _snap(_res("r1"))
    report = diff_baselines(old, new)
    assert report.has_changes
    assert len(report.entries) == 1
    assert report.entries[0].change == "added"
    assert report.entries[0].resource_id == "r1"


def test_diff_removed_resource():
    old = _snap(_res("r1"))
    new = _snap()
    report = diff_baselines(old, new)
    assert len(report.entries) == 1
    assert report.entries[0].change == "removed"


def test_diff_changed_resource():
    from driftwatch.snapshot import fingerprint
    old_attrs = {"state": "running"}
    new_attrs = {"state": "stopped"}
    old = _snap(ResourceSnapshot(resource_id="r1", provider="aws", kind="ec2",
                                  attributes=old_attrs, fingerprint=fingerprint(old_attrs)))
    new = _snap(ResourceSnapshot(resource_id="r1", provider="aws", kind="ec2",
                                  attributes=new_attrs, fingerprint=fingerprint(new_attrs)))
    report = diff_baselines(old, new)
    assert len(report.entries) == 1
    assert report.entries[0].change == "changed"
    assert report.entries[0].old_fingerprint != report.entries[0].new_fingerprint


def test_diff_unchanged_resource():
    r = _res("r1")
    report = diff_baselines(_snap(r), _snap(r))
    assert not report.has_changes


def test_to_dict_structure():
    old = _snap()
    new = _snap(_res("r1"))
    d = diff_baselines(old, new).to_dict()
    assert "has_changes" in d
    assert "summary" in d
    assert "entries" in d
    assert d["entries"][0]["change"] == "added"


def test_summary_counts():
    from driftwatch.snapshot import fingerprint
    r_add = _res("add1")
    r_rem = _res("rem1")
    old_attrs = {"state": "running"}
    new_attrs = {"state": "stopped"}
    r_old = ResourceSnapshot(resource_id="chg1", provider="aws", kind="ec2",
                              attributes=old_attrs, fingerprint=fingerprint(old_attrs))
    r_new = ResourceSnapshot(resource_id="chg1", provider="aws", kind="ec2",
                              attributes=new_attrs, fingerprint=fingerprint(new_attrs))
    old = _snap(r_rem, r_old)
    new = _snap(r_add, r_new)
    report = diff_baselines(old, new)
    assert report.summary() == {"added": 1, "removed": 1, "changed": 1}
