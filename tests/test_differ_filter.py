"""Tests for driftwatch.differ_filter."""
import pytest
from driftwatch.differ import DriftEntry, DriftReport
from driftwatch.differ_filter import (
    DriftFilter,
    _entry_matches,
    filter_report,
    drift_filter_from_dict,
)


def _entry(kind="changed", provider="aws", resource_id="i-001"):
    return DriftEntry(
        kind=kind,
        provider=provider,
        resource_id=resource_id,
        resource_type="instance",
        attribute_diff={},
    )


def _report(*entries):
    return DriftReport(entries=list(entries))


def test_no_filter_matches_all():
    e1, e2 = _entry(), _entry(kind="added", resource_id="i-002")
    result = filter_report(_report(e1, e2), DriftFilter())
    assert len(result.entries) == 2


def test_filter_by_kind():
    e1 = _entry(kind="changed")
    e2 = _entry(kind="added")
    result = filter_report(_report(e1, e2), DriftFilter(kinds=["added"]))
    assert result.entries == [e2]


def test_filter_by_provider():
    e1 = _entry(provider="aws")
    e2 = _entry(provider="gcp")
    result = filter_report(_report(e1, e2), DriftFilter(providers=["gcp"]))
    assert result.entries == [e2]


def test_filter_by_resource_id():
    e1 = _entry(resource_id="i-001")
    e2 = _entry(resource_id="i-002")
    result = filter_report(_report(e1, e2), DriftFilter(resource_ids=["i-001"]))
    assert result.entries == [e1]


def test_filter_by_prefix():
    e1 = _entry(resource_id="prod-server-1")
    e2 = _entry(resource_id="dev-server-1")
    result = filter_report(_report(e1, e2), DriftFilter(resource_id_prefix="prod"))
    assert result.entries == [e1]


def test_combined_filters():
    e1 = _entry(kind="changed", provider="aws", resource_id="i-001")
    e2 = _entry(kind="changed", provider="gcp", resource_id="i-002")
    e3 = _entry(kind="removed", provider="aws", resource_id="i-003")
    f = DriftFilter(kinds=["changed"], providers=["aws"])
    result = filter_report(_report(e1, e2, e3), f)
    assert result.entries == [e1]


def test_drift_filter_from_dict():
    d = {
        "kinds": ["added"],
        "providers": ["azure"],
        "resource_ids": ["vm-1"],
        "resource_id_prefix": "vm",
    }
    f = drift_filter_from_dict(d)
    assert f.kinds == ["added"]
    assert f.providers == ["azure"]
    assert f.resource_ids == ["vm-1"]
    assert f.resource_id_prefix == "vm"


def test_drift_filter_from_dict_defaults():
    f = drift_filter_from_dict({})
    assert f.kinds == []
    assert f.resource_id_prefix is None
