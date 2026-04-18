"""Export drift reports to various output formats (JSON, CSV)."""
from __future__ import annotations

import csv
import io
import json
from typing import List

from driftwatch.differ import DriftReport, DriftEntry


def _entry_to_row(entry: DriftEntry) -> dict:
    changes = "; ".join(
        f"{k}: {v['baseline']!r} -> {v['current']!r}"
        for k, v in (entry.attribute_diff or {}).items()
    )
    return {
        "status": entry.status,
        "resource_id": entry.resource_id,
        "resource_type": entry.resource_type,
        "provider": entry.provider,
        "changes": changes,
    }


def to_json(report: DriftReport, indent: int = 2) -> str:
    """Serialize a DriftReport to a JSON string."""
    data = {
        "provider": report.provider,
        "generated_at": report.generated_at,
        "has_drift": report.has_drift(),
        "summary": report.summary(),
        "entries": [
            {
                "status": e.status,
                "resource_id": e.resource_id,
                "resource_type": e.resource_type,
                "provider": e.provider,
                "attribute_diff": e.attribute_diff or {},
            }
            for e in report.entries
        ],
    }
    return json.dumps(data, indent=indent)


def to_csv(report: DriftReport) -> str:
    """Serialize a DriftReport to a CSV string."""
    fieldnames = ["status", "resource_id", "resource_type", "provider", "changes"]
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for entry in report.entries:
        writer.writerow(_entry_to_row(entry))
    return buf.getvalue()


def export(report: DriftReport, fmt: str) -> str:
    """Export report in the given format ('json' or 'csv')."""
    fmt = fmt.lower()
    if fmt == "json":
        return to_json(report)
    if fmt == "csv":
        return to_csv(report)
    raise ValueError(f"Unsupported export format: {fmt!r}")
