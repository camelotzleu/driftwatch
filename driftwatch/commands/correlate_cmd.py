"""CLI command: correlate drift entries across history runs."""
from __future__ import annotations
import json
import argparse
from driftwatch.history import load as load_history
from driftwatch.differ import DriftReport
from driftwatch.differ_correlator import correlate_reports


def cmd_correlate(args: argparse.Namespace) -> int:
    entries = load_history()
    if not entries:
        print("No history entries found.")
        return 1

    reports = []
    for he in entries:
        report = DriftReport(entries=he.get("entries", []))
        # history entries store raw dicts; rebuild DriftEntry objects
        from driftwatch.differ import DriftEntry
        drift_entries = [
            DriftEntry(
                resource_id=e.get("resource_id", ""),
                kind=e.get("kind", ""),
                provider=e.get("provider", ""),
                change_type=e.get("change_type", "changed"),
                attribute_diff=e.get("attribute_diff", {}),
            )
            for e in he.get("entries", [])
        ]
        reports.append(DriftReport(entries=drift_entries))

    min_co = getattr(args, "min_co_occurrences", 2)
    report = correlate_reports(reports, min_co_occurrences=min_co)

    if args.format == "json":
        print(json.dumps(report.to_dict(), indent=2))
    else:
        if not report.correlations:
            print("No correlations found.")
            return 0
        print(f"Correlations across {report.total_runs} runs (min={min_co}):")
        for c in report.correlations:
            print(f"  [{c.co_occurrences}x]  {c.key_a}  <->  {c.key_b}")

    return 0


def register(subparsers) -> None:
    p = subparsers.add_parser("correlate", help="Find co-occurring drift across history")
    p.add_argument("--min-co-occurrences", type=int, default=2, dest="min_co_occurrences")
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.set_defaults(func=cmd_correlate)
