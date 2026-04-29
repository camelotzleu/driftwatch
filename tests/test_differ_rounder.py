"""Tests for driftwatch.differ_rounder."""
import pytest

from driftwatch.differ import DriftEntry, DriftReport
from driftwatch.differ_rounder import (
    RoundTripResult,
    report_from_dict,
    report_to_dict,
    verify_round_trip,
)


def _entry(
    resource_id: str = "res-1",
    kind: str = "instance",
    provider: str = "aws",
    change_type: str = "changed",
    attribute_diff: dict | None = None,
) -> DriftEntry:
    return DriftEntry(
        resource_id=resource_id,
        kind=kind,
        provider=provider,
        change_type=change_type,
        attribute_diff=attribute_diff or {},
    )


def _report(*entries: DriftEntry, provider: str = "aws") -> DriftReport:
    r = DriftReport(provider=provider)
    for e in entries:
        r.entries.append(e)
    return r


# ---------------------------------------------------------------------------
# report_to_dict
# ---------------------------------------------------------------------------

def test_report_to_dict_empty():
    r = _report(provider="gcp")
    d = report_to_dict(r)
    assert d["provider"] == "gcp"
    assert d["entries"] == []


def test_report_to_dict_single_entry():
    e = _entry(attribute_diff={"size": {"old": "t2.micro", "new": "t3.small"}})
    d = report_to_dict(_report(e))
    assert len(d["entries"]) == 1
    assert d["entries"][0]["resource_id"] == "res-1"
    assert d["entries"][0]["attribute_diff"]["size"]["new"] == "t3.small"


def test_report_to_dict_multiple_entries():
    r = _report(_entry("a"), _entry("b"), _entry("c"))
    d = report_to_dict(r)
    assert len(d["entries"]) == 3


# ---------------------------------------------------------------------------
# report_from_dict
# ---------------------------------------------------------------------------

def test_report_from_dict_empty():
    r = report_from_dict({"provider": "azure", "entries": []})
    assert r.provider == "azure"
    assert r.entries == []


def test_report_from_dict_restores_entry():
    data = {
        "provider": "aws",
        "entries": [
            {
                "resource_id": "i-123",
                "kind": "instance",
                "provider": "aws",
                "change_type": "added",
                "attribute_diff": {},
            }
        ],
    }
    r = report_from_dict(data)
    assert len(r.entries) == 1
    assert r.entries[0].resource_id == "i-123"
    assert r.entries[0].change_type == "added"


def test_report_from_dict_missing_attribute_diff_defaults_empty():
    data = {
        "provider": "aws",
        "entries": [
            {"resource_id": "x", "kind": "bucket", "provider": "aws", "change_type": "removed"}
        ],
    }
    r = report_from_dict(data)
    assert r.entries[0].attribute_diff == {}


# ---------------------------------------------------------------------------
# verify_round_trip
# ---------------------------------------------------------------------------

def test_verify_round_trip_empty_report():
    result = verify_round_trip(_report())
    assert result.ok is True
    assert result.original_count == 0
    assert result.restored_count == 0
    assert result.mismatches == []


def test_verify_round_trip_clean():
    r = _report(
        _entry("r1", change_type="changed", attribute_diff={"k": {"old": "a", "new": "b"}}),
        _entry("r2", change_type="added"),
    )
    result = verify_round_trip(r)
    assert result.ok is True
    assert result.original_count == 2
    assert result.restored_count == 2


def test_verify_round_trip_to_dict_structure():
    result = RoundTripResult(ok=True, original_count=3, restored_count=3, mismatches=[])
    d = result.to_dict()
    assert d["ok"] is True
    assert d["original_count"] == 3
    assert d["mismatches"] == []
