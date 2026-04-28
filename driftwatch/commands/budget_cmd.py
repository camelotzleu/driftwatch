"""CLI command: drift-budget — enforce a per-run drift entry limit."""
from __future__ import annotations

import argparse
import json
import sys

from driftwatch.comparator import compare_to_baseline
from driftwatch.collectors import get_collector
from driftwatch.config import load as load_config
from driftwatch.differ_budgeter import apply_budget


def cmd_budget(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)

    provider_cfg = next(
        (p for p in cfg.providers if p.name == args.provider), None
    )
    if provider_cfg is None:
        print(f"Unknown provider: {args.provider}", file=sys.stderr)
        return 1

    collector = get_collector(provider_cfg)
    snapshot = collector.collect()

    result = compare_to_baseline(snapshot, provider=args.provider)
    if not result.ok:
        print("No baseline found. Run 'driftwatch baseline save' first.", file=sys.stderr)
        return 1

    report = result.report
    priority = args.priority.split(",") if args.priority else None
    budget_report = apply_budget(report, limit=args.limit, priority_change_types=priority)

    if args.format == "json":
        print(json.dumps(budget_report.to_dict(), indent=2))
    else:
        print(f"Drift budget: {budget_report.budget_used}/{budget_report.limit}")
        print(f"Total entries : {budget_report.total_entries}")
        print(f"Over budget   : {budget_report.over_budget}")
        if budget_report.accepted:
            print("\nAccepted entries:")
            for r in budget_report.accepted:
                print(f"  [{r.position:>3}] {r.entry.resource_id} ({r.entry.change_type})")
        if budget_report.rejected:
            print("\nRejected (over-budget) entries:")
            for r in budget_report.rejected:
                print(f"  [{r.position:>3}] {r.entry.resource_id} ({r.entry.change_type})")

    return 1 if budget_report.over_budget else 0


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("budget", help="Enforce a drift entry budget")
    p.add_argument("provider", help="Provider name")
    p.add_argument(
        "--limit", type=int, default=20, help="Maximum allowed drift entries (default: 20)"
    )
    p.add_argument(
        "--priority",
        default=None,
        help="Comma-separated change types to prioritise (default: removed,added)",
    )
    p.add_argument(
        "--format", choices=["text", "json"], default="text", help="Output format"
    )
    p.add_argument("--config", default="driftwatch.yaml")
    p.set_defaults(func=cmd_budget)
