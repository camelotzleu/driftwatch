"""CLI command: classify drift entries by impact level."""
from __future__ import annotations
import json
import argparse
from driftwatch.config import load as load_config
from driftwatch.collectors import get_collector
from driftwatch.comparator import compare_to_baseline
from driftwatch.differ_classifier import classify_report


def cmd_classify(args: argparse.Namespace) -> int:
    cfg = load_config()
    provider_cfg = next(
        (p for p in cfg.providers if p.name == args.provider), None
    )
    if provider_cfg is None:
        print(f"Unknown provider: {args.provider}")
        return 1

    collector = get_collector(provider_cfg)
    snapshot = collector.collect()
    result = compare_to_baseline(snapshot, provider_cfg.name)
    if not result.ok:
        print("No baseline found. Run 'driftwatch baseline save' first.")
        return 1

    report = result.report
    classification = classify_report(report)
    data = classification.to_dict()

    if args.format == "json":
        print(json.dumps(data, indent=2))
    else:
        counts = data["counts"]
        print(f"Classification: {data['total']} entries")
        print(f"  high={counts['high']}  medium={counts['medium']}  low={counts['low']}")
        for e in classification.entries:
            print(f"  [{e.impact.upper():6}] {e.entry.change_type:8} {e.entry.resource_id} ({e.entry.kind})")

    threshold = args.fail_on
    if threshold:
        for e in classification.entries:
            if e.impact == threshold:
                return 2
    return 0


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("classify", help="Classify drift entries by impact level")
    p.add_argument("provider", help="Provider name")
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.add_argument("--fail-on", dest="fail_on", choices=["high", "medium", "low"], default=None,
                   help="Exit with code 2 if any entry matches this impact level")
    p.set_defaults(func=cmd_classify)
