"""Correlate drift entries across multiple reports to find co-occurring changes."""
from __future__ import annotations
from dataclasses import dataclass, field
from collections import defaultdict
from typing import List, Dict, Tuple
from driftwatch.differ import DriftReport, DriftEntry


@dataclass
class Correlation:
    key_a: str  # "provider:kind:resource_id"
    key_b: str
    co_occurrences: int

    def to_dict(self) -> dict:
        return {
            "key_a": self.key_a,
            "key_b": self.key_b,
            "co_occurrences": self.co_occurrences,
        }


@dataclass
class CorrelationReport:
    correlations: List[Correlation] = field(default_factory=list)
    total_runs: int = 0

    def to_dict(self) -> dict:
        return {
            "total_runs": self.total_runs,
            "correlations": [c.to_dict() for c in self.correlations],
        }


def _entry_key(e: DriftEntry) -> str:
    return f"{e.provider}:{e.kind}:{e.resource_id}"


def correlate_reports(
    reports: List[DriftReport], min_co_occurrences: int = 2
) -> CorrelationReport:
    """Find pairs of resources that drift together across multiple reports."""
    run_sets: List[set] = []
    for report in reports:
        keys = {_entry_key(e) for e in report.entries}
        if keys:
            run_sets.append(keys)

    pair_counts: Dict[Tuple[str, str], int] = defaultdict(int)
    for keys in run_sets:
        sorted_keys = sorted(keys)
        for i in range(len(sorted_keys)):
            for j in range(i + 1, len(sorted_keys)):
                pair_counts[(sorted_keys[i], sorted_keys[j])] += 1

    correlations = [
        Correlation(key_a=a, key_b=b, co_occurrences=count)
        for (a, b), count in sorted(pair_counts.items(), key=lambda x: -x[1])
        if count >= min_co_occurrences
    ]

    return CorrelationReport(correlations=correlations, total_runs=len(run_sets))
