"""Tests for driftwatch.differ_ranker."""
import pytest
from driftwatch.differ import DriftEntry, DriftReport
from driftwatch.differ_ranker import rank_report, _score_entry, RankReport


def _entry(change_type="changed", kind="instance", provider="aws", rid="r1", attr_diff=None):
    return DriftEntry(
        resource_id=rid,
        kind=kind,
        provider=provider,
        change_type=change_type,
        attribute_diff=attr_diff or {},
    )


def _report(*entries):
    r = DriftReport()
    for e in entries:
        r.entries.append(e)
    return r


def test_rank_empty_report():
    result = rank_report(_report())
    assert isinstance(result, RankReport)
    assert result.ranked == []


def test_score_added_removed_higher_than_changed():
    added = _entry(change_type="added")
    removed = _entry(change_type="removed")
    changed = _entry(change_type="changed")
    assert _score_entry(added) > _score_entry(changed)
    assert _score_entry(removed) > _score_entry(changed)


def test_score_high_impact_key_bonus():
    with_key = _entry(attr_diff={"instance_type": {"old": "t2.micro", "new": "t3.large"}})
    without_key = _entry(attr_diff={"tags": {"old": "a", "new": "b"}})
    assert _score_entry(with_key) > _score_entry(without_key)


def test_rank_orders_by_score_descending():
    low = _entry(change_type="changed", rid="low")
    high = _entry(change_type="added", rid="high")
    result = rank_report(_report(low, high))
    assert result.ranked[0].entry.resource_id == "high"
    assert result.ranked[1].entry.resource_id == "low"


def test_rank_top_n_limits_results():
    entries = [_entry(rid=f"r{i}", change_type="added") for i in range(5)]
    result = rank_report(_report(*entries), top_n=3)
    assert len(result.ranked) == 3


def test_to_dict_structure():
    e = _entry(change_type="changed", attr_diff={"size": {"old": "1", "new": "2"}})
    result = rank_report(_report(e))
    d = result.to_dict()
    assert "ranked" in d
    assert d["ranked"][0]["score"] > 0
    assert "attribute_diff" in d["ranked"][0]


def test_score_multiple_attr_diff_keys():
    e = _entry(attr_diff={"a": {}, "b": {}, "c": {}})
    score = _score_entry(e)
    assert score == round(1 + 3 * 0.5, 2)
