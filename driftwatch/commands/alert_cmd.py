"""CLI command: evaluate alerting rules against the latest drift report."""
from __future__ import annotations
import argparse
import json
import sys
from driftwatch import baseline, config
from driftwatch.collectors import get_collector
from driftwatch.differ import compare
from driftwatch.alerting import evaluate, rules_from_dict
from driftwatch.reporter import render


def cmd_alert(args: argparse.Namespace) -> int:
    cfg = config.load(args.config)

    rules_data = []
    if args.rules:
        with open(args.rules) as f:
            rules_data = json.load(f)
    elif cfg.raw.get("alerting", {}).get("rules"):
        rules_data = cfg.raw["alerting"]["rules"]

    if not rules_data:
        print("No alerting rules configured.", file=sys.stderr)
        return 1

    rules = rules_from_dict(rules_data)

    collector = get_collector(cfg.provider)
    current = collector.collect()
    saved = baseline.load(cfg.provider.name)

    if saved is None:
        print("No baseline found. Run 'driftwatch baseline save' first.", file=sys.stderr)
        return 1

    report = compare(saved, current)
    results = evaluate(report, rules)

    triggered = [r for r in results if r.triggered]
    if not triggered:
        print("No alert rules triggered.")
        return 0

    for result in triggered:
        print(f"[{result.severity.upper()}] Rule '{result.rule.name}' triggered: "
              f"{len(result.matched_entries)} matching change(s).")

    return 2  # non-zero signals drift to CI pipelines


def register(subparsers):
    p = subparsers.add_parser("alert", help="Evaluate alerting rules against current drift")
    p.add_argument("--config", default="driftwatch.yaml", help="Config file path")
    p.add_argument("--rules", default=None, help="JSON file containing alert rules")
    p.set_defaults(func=cmd_alert)
