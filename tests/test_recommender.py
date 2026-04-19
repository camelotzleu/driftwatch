"""Tests for driftwatch.recommender."""
import pytest
from driftwatch.differ import DriftEntry, DriftReport
from driftwatch.recommender import recommend, Recommendation, RecommendationReport


def _entry(change_type: str, attr_diff=None) -> DriftEntry:
    return DriftEntry(
        resource_id="res-1",
        provider="aws",
        kind="ec2_instance",
        change_type=change_type,
        attribute_diff=attr_diff,
    )


def _report(*entries) -> DriftReport:
    r = DriftReport()
    for e in entries:
        r.entries.append(e)
    return r


def test_recommend_empty_report():
    result = recommend(_report())
    assert isinstance(result, RecommendationReport)
    assert result.recommendations == []


def test_recommend_added_entry():
    result = recommend(_report(_entry("added")))
    assert len(result.recommendations) == 1
    rec = result.recommendations[0]
    assert rec.change_type == "added"
    assert "baseline" in rec.action.lower() or "remove" in rec.action.lower()
    assert rec.detail is None


def test_recommend_removed_entry():
    result = recommend(_report(_entry("removed")))
    rec = result.recommendations[0]
    assert rec.change_type == "removed"
    assert "restore" in rec.action.lower() or "re-provision" in rec.action.lower()


def test_recommend_changed_entry_with_diff():
    diff = {"instance_type": {"baseline": "t2.micro", "current": "t3.medium"}}
    result = recommend(_report(_entry("changed", attr_diff=diff)))
    rec = result.recommendations[0]
    assert rec.change_type == "changed"
    assert rec.detail is not None
    assert "instance_type" in rec.detail


def test_recommend_changed_entry_no_diff():
    result = recommend(_report(_entry("changed", attr_diff={})))
    rec = result.recommendations[0]
    assert rec.detail is None


def test_recommendation_to_dict():
    result = recommend(_report(_entry("added")))
    d = result.to_dict()
    assert "recommendations" in d
    assert d["recommendations"][0]["resource_id"] == "res-1"
    assert d["recommendations"][0]["provider"] == "aws"


def test_recommend_multiple_entries():
    entries = [_entry("added"), _entry("removed"), _entry("changed", {"x": {}})]
    result = recommend(_report(*entries))
    assert len(result.recommendations) == 3
    types = {r.change_type for r in result.recommendations}
    assert types == {"added", "removed", "changed"}
