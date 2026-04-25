"""CLI command: driftwatch escalate — show escalated drift entries."""
from __future__ import annotations

import argparse
import json
import sys

from driftwatch.commands import register_all  # noqa: F401 – side-effect import guard
from driftwatch.config import load as load_config
from driftwatch.collectors import get_collector
from driftwatch.baseline import load as load_baseline
from driftwatch.differ import compare
from driftwatch.differ_escalator import escalate_report


def cmd_escalate(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    provider_cfg = next(
        (p for p in cfg.providers if p.name == args.provider), None
    )
    if provider_cfg is None:
        print(f"Unknown provider: {args.provider}", file=sys.stderr)
        return 1

    baseline = load_baseline(provider=args.provider)
    if baseline is None:
        print("No baseline found. Run 'driftwatch baseline save' first.", file=sys.stderr)
        return 1

    collector = get_collector(provider_cfg)
    current = collector.collect()
    report = compare(baseline, current)

    escalation = escalate_report(report, threshold=args.threshold)

    if args.format == "json":
        print(json.dumps(escalation.to_dict(), indent=2))
    else:
        d = escalation.to_dict()
        print(f"Escalation report  threshold={d['threshold']}")
        print(f"  Total entries  : {d['total']}")
        print(f"  Escalated      : {d['escalated_count']}")
        for e in d["entries"]:
            flag = "[!]" if e["escalated"] else "[ ]"
            print(
                f"  {flag} {e['resource_id']} ({e['kind']}/{e['provider']}) "
                f"runs={e['consecutive_runs']} — {e['escalation_reason']}"
            )

    return 1 if escalation.to_dict()["escalated_count"] > 0 else 0


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("escalate", help="Show escalated (persistent) drift entries")
    p.add_argument("provider", help="Provider name to check")
    p.add_argument(
        "--threshold",
        type=int,
        default=3,
        help="Consecutive runs before escalation (default: 3)",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format",
    )
    p.add_argument("--config", default="driftwatch.yaml", help="Config file path")
    p.set_defaults(func=cmd_escalate)
