"""Tests for driftwatch.differ_sampler."""
from __future__ import annotations

import pytest

from driftwatch.differ import DriftEntry, DriftReport
from driftwatch.differ_sampler import SampleReport, SampledEntry, sample_report


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _entry(resource_id: str = "r-1", kind: str = "vm", provider: str = "aws") -> DriftEntry:
    return DriftEntry(
        resource_id=resource_id,
        kind=kind,
        provider=provider,
        change_type="changed",
        attribute_diff={"state": {"baseline": "running", "current": "stopped"}},
    )


def _report(*ids: str) -> DriftReport:
    entries = [_entry(resource_id=rid) for rid in ids]
    return DriftReport(entries=entries)


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------

def test_sample_empty_report():
    report = _report()
    result = sample_report(report, fraction=0.5)
    assert isinstance(result, SampleReport)
    assert result.total_entries == 0
    assert result.sampled_count == 0
    assert result.entries == []


def test_sample_full_fraction():
    report = _report("r-1", "r-2", "r-3", "r-4")
    result = sample_report(report, fraction=1.0, seed=0)
    assert result.sampled_count == 4
    assert result.total_entries == 4


def test_sample_zero_fraction():
    report = _report("r-1", "r-2", "r-3")
    result = sample_report(report, fraction=0.0, seed=0)
    assert result.sampled_count == 0


def test_sample_half_fraction():
    report = _report("r-1", "r-2", "r-3", "r-4")
    result = sample_report(report, fraction=0.5, seed=42)
    assert result.sampled_count == 2
    assert len(result.entries) == 2


def test_sample_reproducible_with_seed():
    report = _report("r-1", "r-2", "r-3", "r-4", "r-5", "r-6")
    result_a = sample_report(report, fraction=0.5, seed=7)
    result_b = sample_report(report, fraction=0.5, seed=7)
    ids_a = [e.entry.resource_id for e in result_a.entries]
    ids_b = [e.entry.resource_id for e in result_b.entries]
    assert ids_a == ids_b


def test_sample_different_seeds_differ():
    report = _report(*[f"r-{i}" for i in range(20)])
    result_a = sample_report(report, fraction=0.5, seed=1)
    result_b = sample_report(report, fraction=0.5, seed=2)
    ids_a = {e.entry.resource_id for e in result_a.entries}
    ids_b = {e.entry.resource_id for e in result_b.entries}
    # With 20 resources it's overwhelmingly likely the samples differ
    assert ids_a != ids_b


def test_sample_entries_are_sampled_entry_instances():
    report = _report("r-1", "r-2", "r-3")
    result = sample_report(report, fraction=1.0, seed=0)
    for item in result.entries:
        assert isinstance(item, SampledEntry)


def test_sample_index_assigned():
    report = _report("r-1", "r-2", "r-3")
    result = sample_report(report, fraction=1.0, seed=0)
    indices = [e.sample_index for e in result.entries]
    assert indices == list(range(len(result.entries)))


def test_to_dict_structure():
    report = _report("r-1", "r-2")
    result = sample_report(report, fraction=1.0, seed=0)
    d = result.to_dict()
    assert "total_entries" in d
    assert "sampled_count" in d
    assert "fraction" in d
    assert "seed" in d
    assert "entries" in d
    assert isinstance(d["entries"], list)


def test_invalid_fraction_raises():
    report = _report("r-1")
    with pytest.raises(ValueError, match="fraction"):
        sample_report(report, fraction=1.5)
    with pytest.raises(ValueError, match="fraction"):
        sample_report(report, fraction=-0.1)


def test_to_dict_entry_has_attribute_diff():
    report = _report("r-1")
    result = sample_report(report, fraction=1.0, seed=0)
    entry_dict = result.to_dict()["entries"][0]
    assert "attribute_diff" in entry_dict
