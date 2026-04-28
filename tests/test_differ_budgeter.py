"""Tests for driftwatch.differ_budgeter."""
from __future__ import annotations

from driftwatch.differ import DriftEntry, DriftReport
from driftwatch.differ_budgeter import apply_budget, BudgetReport, BudgetResult


def _entry(resource_id: str, change_type: str = "changed") -> DriftEntry:
    return DriftEntry(
        resource_id=resource_id,
        kind="Instance",
        provider="aws",
        change_type=change_type,
        attribute_diff={},
    )


def _report(*entries: DriftEntry) -> DriftReport:
    r = DriftReport()
    for e in entries:
        r.entries.append(e)
    return r


def test_budget_empty_report():
    br = apply_budget(_report(), limit=5)
    assert isinstance(br, BudgetReport)
    assert br.total_entries == 0
    assert br.budget_used == 0
    assert not br.over_budget
    assert br.accepted == []
    assert br.rejected == []


def test_budget_within_limit():
    r = _report(_entry("r1"), _entry("r2"), _entry("r3"))
    br = apply_budget(r, limit=5)
    assert br.total_entries == 3
    assert br.budget_used == 3
    assert not br.over_budget
    assert len(br.rejected) == 0


def test_budget_exactly_at_limit():
    r = _report(_entry("r1"), _entry("r2"))
    br = apply_budget(r, limit=2)
    assert not br.over_budget
    assert br.budget_used == 2
    assert len(br.rejected) == 0


def test_budget_over_limit():
    r = _report(_entry("r1"), _entry("r2"), _entry("r3"), _entry("r4"))
    br = apply_budget(r, limit=2)
    assert br.over_budget
    assert br.budget_used == 2
    assert len(br.rejected) == 2


def test_priority_change_types_ranked_first():
    r = _report(
        _entry("c1", "changed"),
        _entry("a1", "added"),
        _entry("rm1", "removed"),
    )
    br = apply_budget(r, limit=2, priority_change_types=["removed", "added"])
    accepted_ids = [res.entry.resource_id for res in br.accepted]
    # removed and added should come before changed
    assert "rm1" in accepted_ids
    assert "a1" in accepted_ids
    assert "c1" not in accepted_ids


def test_position_is_1_based():
    r = _report(_entry("r1"), _entry("r2"), _entry("r3"))
    br = apply_budget(r, limit=10)
    positions = [res.position for res in br.accepted]
    assert positions == [1, 2, 3]


def test_to_dict_structure():
    r = _report(_entry("r1", "added"), _entry("r2", "changed"))
    br = apply_budget(r, limit=1)
    d = br.to_dict()
    assert d["limit"] == 1
    assert d["total_entries"] == 2
    assert d["over_budget"] is True
    assert len(d["accepted"]) == 1
    assert len(d["rejected"]) == 1
    accepted = d["accepted"][0]
    assert "resource_id" in accepted
    assert "within_budget" in accepted
    assert accepted["within_budget"] is True


def test_budget_result_to_dict():
    entry = _entry("x1", "removed")
    result = BudgetResult(entry=entry, within_budget=False, position=5)
    d = result.to_dict()
    assert d["resource_id"] == "x1"
    assert d["change_type"] == "removed"
    assert d["within_budget"] is False
    assert d["position"] == 5
