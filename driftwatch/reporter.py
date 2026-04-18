"""Formats and outputs DriftReport results to console or file."""
from __future__ import annotations

import json
import sys
from typing import IO, Literal

from driftwatch.differ import DriftReport

OutputFormat = Literal["text", "json"]


def _text_lines(report: DriftReport) -> list[str]:
    lines: list[str] = []
    if not report.has_drift():
        lines.append("✓ No drift detected.")
        return lines

    lines.append(f"⚠ Drift detected: {report.summary()}")
    lines.append("")

    for entry in report.entries:
        lines.append(f"  [{entry.status.upper()}] {entry.resource_type}/{entry.resource_id}")
        if entry.status == "changed":
            for attr, (old, new) in entry.attribute_diffs.items():
                lines.append(f"      {attr}: {old!r} → {new!r}")
        lines.append("")

    return lines


def _report_to_dict(report: DriftReport) -> dict:
    return {
        "has_drift": report.has_drift(),
        "summary": report.summary(),
        "entries": [
            {
                "resource_id": e.resource_id,
                "resource_type": e.resource_type,
                "status": e.status,
                "attribute_diffs": {
                    k: {"old": v[0], "new": v[1]}
                    for k, v in e.attribute_diffs.items()
                },
            }
            for e in report.entries
        ],
    }


def render(
    report: DriftReport,
    fmt: OutputFormat = "text",
    out: IO[str] | None = None,
) -> None:
    """Write report to *out* (defaults to stdout)."""
    if out is None:
        out = sys.stdout

    if fmt == "json":
        json.dump(_report_to_dict(report), out, indent=2)
        out.write("\n")
    else:
        for line in _text_lines(report):
            out.write(line + "\n")
