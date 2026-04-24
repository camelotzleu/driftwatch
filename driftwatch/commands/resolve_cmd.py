"""CLI command: resolve drift entries by resource ID."""
from __future__ import annotations

import argparse
import json
import sys

from driftwatch.collectors import get_collector
from driftwatch.comparator import compare_to_baseline
from driftwatch.config import DriftWatchConfig
from driftwatch.differ_resolver import resolve_report


def cmd_resolve(args: argparse.Namespace, cfg: DriftWatchConfig) -> int:
    provider_cfg = next(
        (p for p in cfg.providers if p.name == args.provider), None
    )
    if provider_cfg is None:
        print(f"Unknown provider: {args.provider}", file=sys.stderr)
        return 1

    collector = get_collector(provider_cfg)
    snapshot = collector.collect()

    result = compare_to_baseline(snapshot, provider_cfg.name)
    if not result.ok:
        print(result.message, file=sys.stderr)
        return 1

    report = result.report
    if not report.has_drift():
        print("No drift detected — nothing to resolve.")
        return 0

    resource_ids = args.resource_ids
    resolution = resolve_report(
        report,
        resource_ids=resource_ids,
        resolved_by=args.resolved_by,
        note=args.note or "",
    )

    if args.format == "json":
        print(json.dumps(resolution.to_dict(), indent=2))
    else:
        d = resolution.to_dict()
        print(f"Resolved : {d['total_resolved']}")
        print(f"Unresolved: {d['total_unresolved']}")
        for r in d["resolved"]:
            print(
                f"  [resolved] {r['resource_id']} ({r['change_type']}) "
                f"by {r['resolved_by']} at {r['resolved_at']}"
            )
        for u in d["unresolved"]:
            print(f"  [open]     {u['resource_id']} ({u['change_type']})")

    return 0


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("resolve", help="Mark drift entries as resolved")
    p.add_argument("provider", help="Provider name")
    p.add_argument("resource_ids", nargs="+", help="Resource IDs to resolve")
    p.add_argument("--resolved-by", default="cli", help="Who resolved the drift")
    p.add_argument("--note", default="", help="Optional resolution note")
    p.add_argument(
        "--format", choices=["text", "json"], default="text", help="Output format"
    )
    p.set_defaults(func=cmd_resolve)
