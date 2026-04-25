"""CLI command: driftwatch throttle

Apply throttle rules to the latest drift report and print which entries
would be suppressed versus forwarded.
"""
from __future__ import annotations

import argparse
import sys
from typing import List

from driftwatch.collectors import get_collector
from driftwatch.comparator import compare_to_baseline
from driftwatch.config import DriftWatchConfig
from driftwatch.differ_throttler import ThrottleRule, throttle_report
from driftwatch.reporter import render


def _rules_from_config(cfg: DriftWatchConfig) -> List[ThrottleRule]:
    raw = getattr(cfg, "throttle_rules", []) or []
    rules = []
    for item in raw:
        rules.append(
            ThrottleRule(
                resource_id=item.get("resource_id"),
                kind=item.get("kind"),
                provider=item.get("provider"),
                cooldown_seconds=int(item.get("cooldown_seconds", 3600)),
            )
        )
    return rules


def cmd_throttle(args: argparse.Namespace, cfg: DriftWatchConfig) -> int:
    provider_name = args.provider
    try:
        collector = get_collector(provider_name, cfg)
    except KeyError:
        print(f"Unknown provider: {provider_name}", file=sys.stderr)
        return 1

    snapshot = collector.collect()
    result = compare_to_baseline(snapshot, provider=provider_name)
    if not result.ok:
        print("No baseline found. Run 'driftwatch baseline save' first.", file=sys.stderr)
        return 1

    report = result.report
    rules = _rules_from_config(cfg)
    throttle_result = throttle_report(report, rules)

    fmt = getattr(args, "format", "text")
    if fmt == "json":
        import json
        print(json.dumps(throttle_result.to_dict(), indent=2))
    else:
        print(f"Allowed  : {len(throttle_result.allowed)}")
        print(f"Suppressed: {len(throttle_result.suppressed)}")
        for e in throttle_result.suppressed:
            print(f"  [suppressed] {e.provider}/{e.kind}/{e.resource_id}")

    return 0


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "throttle",
        help="Apply throttle rules to suppress repeated drift alerts",
    )
    p.add_argument("provider", help="Cloud provider name (aws, gcp, azure, mock)")
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format",
    )
    p.set_defaults(func=cmd_throttle)
