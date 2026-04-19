"""Tests for differ_correlator."""
import pytest
from driftwatch.differ import DriftReport, DriftEntry
from driftwatch.differ_correlator import correlate_reports, Correlation, CorrelationReport


def _entry(resource_id: str, provider: str = "aws", kind: str = "ec2") -> DriftEntry:
    return DriftEntry(
        resource_id=resource_id,
        kind=kind,
        provider=provider,
        change_type="changed",
        attribute_diff={},
    )


def _report(*resource_ids) -> DriftReport:
    return DriftReport(entries=[_entry(r) for r in resource_ids])


def test_correlate_empty_reports():
    result = correlate_reports([])
    assert isinstance(result, CorrelationReport)
    assert result.correlations == []
    assert result.total_runs == 0


def test_correlate_single_report_no_pairs():
    result = correlate_reports([_report("i-1")])
    assert result.correlations == []
    assert result.total_runs == 1


def test_correlate_two_resources_co_occur():
    reports = [_report("i-1", "i-2"), _report("i-1", "i-2"), _report("i-1")]
    result = correlate_reports(reports, min_co_occurrences=2)
    assert len(result.correlations) == 1
    c = result.correlations[0]
    assert c.co_occurrences == 2
    assert "i-1" in c.key_a or "i-1" in c.key_b
    assert "i-2" in c.key_a or "i-2" in c.key_b


def test_correlate_below_threshold_excluded():
    reports = [_report("i-1", "i-2"), _report("i-3")]
    result = correlate_reports(reports, min_co_occurrences=2)
    assert result.correlations == []


def test_correlate_multiple_pairs_sorted_by_count():
    reports = [
        _report("i-1", "i-2", "i-3"),
        _report("i-1", "i-2", "i-3"),
        _report("i-1", "i-3"),
    ]
    result = correlate_reports(reports, min_co_occurrences=2)
    counts = [c.co_occurrences for c in result.correlations]
    assert counts == sorted(counts, reverse=True)
    assert result.total_runs == 3


def test_to_dict_structure():
    reports = [_report("i-1", "i-2"), _report("i-1", "i-2")]
    result = correlate_reports(reports, min_co_occurrences=2)
    d = result.to_dict()
    assert "total_runs" in d
    assert "correlations" in d
    assert d["correlations"][0]["co_occurrences"] == 2
