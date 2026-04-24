"""CLI command: apply ignore rules to a drift report."""
from __future__ import annotations

import argparse
import json
import sys

from driftwatch.collectors import get_collector
from driftwatch.comparator import compare_to_baseline
from driftwatch.config import load as load_config
from driftwatch.differ_ignorer import ignore_report, ignore_rules_from_list


def cmd_ignore(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    provider_cfg = next(
        (p for p in cfg.providers if p.name == args.provider), None
    )
    if provider_cfg is None:
        print(f"Unknown provider: {args.provider}", file=sys.stderr)
        return 1

    collector = get_collector(provider_cfg)
    result = compare_to_baseline(collector, provider_cfg)
    if not result.ok:
        print(result.message, file=sys.stderr)
        return 1

    raw_rules = cfg.raw.get("ignore_rules", [])
    if args.rules_file:
        try:
            with open(args.rules_file) as fh:
                raw_rules = json.load(fh)
        except (OSError, json.JSONDecodeError) as exc:
            print(f"Failed to load rules file: {exc}", file=sys.stderr)
            return 1

    rules = ignore_rules_from_list(raw_rules)
    ignore_result = ignore_report(result.report, rules)

    if args.format == "json":
        print(json.dumps(ignore_result.to_dict(), indent=2))
    else:
        print(f"Kept:    {len(ignore_result.kept)}")
        print(f"Ignored: {len(ignore_result.ignored)}")
        for entry in ignore_result.ignored:
            reason = ignore_result.ignored_reasons.get(entry.resource_id, "")
            tag = f" ({reason})" if reason else ""
            print(f"  - [{entry.provider}] {entry.resource_id} ({entry.kind}){tag}")

    return 0


def register(subparsers) -> None:
    p = subparsers.add_parser("ignore", help="Apply ignore rules to a drift report")
    p.add_argument("provider", help="Provider name")
    p.add_argument("--config", default="driftwatch.yaml")
    p.add_argument("--rules-file", dest="rules_file", default=None,
                   help="JSON file containing ignore rules")
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.set_defaults(func=cmd_ignore)
