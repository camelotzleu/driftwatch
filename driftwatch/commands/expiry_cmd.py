"""CLI command: driftwatch expiry — flag drift entries that have exceeded a TTL."""
from __future__ import annotations

import argparse
import json
import sys

from driftwatch.collectors import get_collector
from driftwatch.baseline import load as load_baseline
from driftwatch.differ import compare
from driftwatch.differ_expirer import check_expiry


def cmd_expiry(args: argparse.Namespace, cfg) -> int:
    provider_cfg = next(
        (p for p in cfg.providers if p.name == args.provider), None
    )
    if provider_cfg is None:
        print(f"Unknown provider: {args.provider}", file=sys.stderr)
        return 1

    baseline = load_baseline(args.provider)
    if baseline is None:
        print(
            f"No baseline found for provider '{args.provider}'. "
            "Run 'driftwatch baseline save' first.",
            file=sys.stderr,
        )
        return 1

    collector = get_collector(provider_cfg)
    current = collector.collect()
    report = compare(baseline, current)

    ttl = getattr(args, "ttl", 7)
    expiry_report = check_expiry(report, ttl_days=ttl)

    if args.format == "json":
        print(json.dumps(expiry_report.to_dict(), indent=2))
    else:
        d = expiry_report.to_dict()
        print(f"Expiry check — TTL: {ttl} days")
        print(f"  Total drift entries : {d['total']}")
        print(f"  Expired entries     : {d['expired_count']}")
        if d["entries"]:
            print()
            for e in d["entries"]:
                marker = "[EXPIRED]" if e["expired"] else "[ok]"
                print(
                    f"  {marker:10s} {e['resource_id']} "
                    f"({e['kind']}/{e['provider']}) "
                    f"age={e['age_days']}d first_seen={e['first_seen'] or 'unknown'}"
                )

    expired_count = expiry_report.to_dict()["expired_count"]
    return 1 if expired_count > 0 else 0


def register(subparsers) -> None:
    p = subparsers.add_parser(
        "expiry",
        help="Flag drift entries that have persisted beyond a TTL",
    )
    p.add_argument("provider", help="Provider name (aws, gcp, azure, mock)")
    p.add_argument(
        "--ttl",
        type=int,
        default=7,
        metavar="DAYS",
        help="Days before a drift entry is considered expired (default: 7)",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    p.set_defaults(func=cmd_expiry)
