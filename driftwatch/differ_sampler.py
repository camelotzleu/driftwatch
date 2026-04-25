"""Drift sampler: randomly sample a fraction of drift entries for spot-checking."""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import List, Optional

from driftwatch.differ import DriftEntry, DriftReport


@dataclass
class SampledEntry:
    entry: DriftEntry
    sample_index: int

    def to_dict(self) -> dict:
        d = {
            "resource_id": self.entry.resource_id,
            "kind": self.entry.kind,
            "provider": self.entry.provider,
            "change_type": self.entry.change_type,
            "sample_index": self.sample_index,
        }
        if self.entry.attribute_diff:
            d["attribute_diff"] = self.entry.attribute_diff
        return d


@dataclass
class SampleReport:
    total_entries: int
    sampled_count: int
    fraction: float
    seed: Optional[int]
    entries: List[SampledEntry] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "total_entries": self.total_entries,
            "sampled_count": self.sampled_count,
            "fraction": self.fraction,
            "seed": self.seed,
            "entries": [e.to_dict() for e in self.entries],
        }


def sample_report(
    report: DriftReport,
    fraction: float = 0.5,
    seed: Optional[int] = None,
) -> SampleReport:
    """Return a SampleReport containing a random sample of drift entries.

    Args:
        report:   The source DriftReport to sample from.
        fraction: Proportion of entries to include (0.0 – 1.0).
        seed:     Optional RNG seed for reproducibility.
    """
    if not 0.0 <= fraction <= 1.0:
        raise ValueError(f"fraction must be between 0.0 and 1.0, got {fraction}")

    all_entries = report.entries
    total = len(all_entries)

    rng = random.Random(seed)
    k = max(0, round(total * fraction))
    chosen = rng.sample(all_entries, k) if k <= total else list(all_entries)

    sampled = [
        SampledEntry(entry=e, sample_index=i) for i, e in enumerate(chosen)
    ]

    return SampleReport(
        total_entries=total,
        sampled_count=len(sampled),
        fraction=fraction,
        seed=seed,
        entries=sampled,
    )
