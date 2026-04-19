"""Tests for driftwatch.differ_grouper."""
import pytest
from driftwatch.differ import DriftEntry, DriftReport
from driftwatch.differ_grouper import group_report, DriftGroup, GroupReport


def _entry(resource_id: str, kind: str, provider: str, change_type: str) -> DriftEntry:
    return DriftEntry(
        resource_id=resource_id,
        kind=kind,
        provider=provider,
        change_type=change_type,
        attribute_diff={},
    )


def _report(*entries: DriftEntry) -> DriftReport:
    return DriftReport(entries=list(entries))


def test_group_empty_report():
    r = group_report(_report(), group_by="kind")
    assert isinstance(r, GroupReport)
    assert r.groups == {}
    assert r.group_by == "kind"


def test_group_by_kind():
    r = group_report(
        _report(
            _entry("i-1", "ec2", "aws", "changed"),
            _entry("i-2", "ec2", "aws", "added"),
            _entry("b-1", "s3", "aws", "removed"),
        ),
        group_by="kind",
    )
    assert set(r.groups.keys()) == {"ec2", "s3"}
    assert len(r.groups["ec2"].entries) == 2
    assert len(r.groups["s3"].entries) == 1


def test_group_by_provider():
    r = group_report(
        _report(
            _entry("i-1", "ec2", "aws", "changed"),
            _entry("vm-1", "vm", "azure", "added"),
        ),
        group_by="provider",
    )
    assert set(r.groups.keys()) == {"aws", "azure"}


def test_group_by_change_type():
    r = group_report(
        _report(
            _entry("i-1", "ec2", "aws", "changed"),
            _entry("i-2", "ec2", "aws", "added"),
            _entry("i-3", "ec2", "aws", "added"),
        ),
        group_by="change_type",
    )
    assert r.groups["added"].count == 2
    assert r.groups["changed"].count == 1


def test_to_dict_structure():
    r = group_report(
        _report(_entry("i-1", "ec2", "aws", "changed")),
        group_by="kind",
    )
    d = r.to_dict()
    assert d["group_by"] == "kind"
    assert "ec2" in d["groups"]
    grp = d["groups"]["ec2"]
    assert grp["count"] == 1
    assert grp["entries"][0]["resource_id"] == "i-1"


def test_invalid_group_by_raises():
    with pytest.raises(ValueError):
        group_report(_report(_entry("x", "ec2", "aws", "added")), group_by="bogus")  # type: ignore
