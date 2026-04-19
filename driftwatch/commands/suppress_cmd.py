"""CLI command: suppress known drift using rules from config."""
from __future__ import annotations

import argparse
import json
import sys

from driftwatch import baseline, collector_utils
from driftwatch.config import load as load_config
from driftwatch.differ import compare
from driftwatch.suppressor import suppression_rules_from_dict, suppress_report
from driftwatch.reporter import render


def cmd_suppress(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    snap = baseline.load(cfg)
    if snap is None:
        print("No baseline found. Run 'driftwatch baseline save' first.", file=sys.stderr)
        return 1

    rules_data = getattr(cfg, "suppression_rules", []) or []
    rules = suppression_rules_from_dict(rules_data)
    if not rules:
        print("No suppression rules configured.", file=sys.stderr)
        return 1

    from driftwatch.collectors import get_collector
    collector = get_collector(cfg.provider)
    current = collector.collect(cfg.provider)
    report = compare(snap, current)

    result = suppress_report(report, rules)

    if args.format == "json":
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(f"Suppressed: {len(result.suppressed)}  Kept: {len(result.kept)}")
        for e in result.suppressed:
            print(f"  [suppressed] {e.provider}/{e.kind}/{e.resource_id}")

    return 0 if not result.kept else 2


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("suppress", help="Apply suppression rules to current drift")
    p.add_argument("--config", default="driftwatch.yaml")
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.set_defaults(func=cmd_suppress)
