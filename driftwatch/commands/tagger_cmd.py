"""CLI sub-command: filter a baseline diff by tags and render the result."""
from __future__ import annotations
import argparse
import json
import sys

from driftwatch import baseline, reporter
from driftwatch.collectors import get_collector
from driftwatch.config import load as load_config
from driftwatch.differ import compare
from driftwatch.tagger import TagFilter, filter_report


def cmd_tag_filter(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    provider_cfg = cfg.providers[0] if cfg.providers else None
    if provider_cfg is None:
        print("No provider configured.", file=sys.stderr)
        return 1

    saved = baseline.load(provider_cfg.name)
    if saved is None:
        print("No baseline found. Run 'driftwatch baseline save' first.", file=sys.stderr)
        return 1

    collector = get_collector(provider_cfg)
    current = collector.collect()
    report = compare(saved, current)

    required = _parse_tags(args.require or [])
    excluded = _parse_tags(args.exclude or [])
    tf = TagFilter(required=required, excluded=excluded)
    filtered = filter_report(report, tf)

    output = reporter.render(filtered, fmt=args.format)
    print(output)
    return 0


def _parse_tags(pairs: list) -> dict:
    result = {}
    for pair in pairs:
        if "=" not in pair:
            continue
        k, v = pair.split("=", 1)
        result[k.strip()] = v.strip()
    return result


def register(subparsers) -> None:
    p = subparsers.add_parser("tag-filter", help="Filter drift report by resource tags")
    p.add_argument("--require", nargs="*", metavar="KEY=VALUE",
                   help="Only include resources with these tags")
    p.add_argument("--exclude", nargs="*", metavar="KEY=VALUE",
                   help="Exclude resources with these tags")
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.add_argument("--config", default="driftwatch.yaml")
    p.set_defaults(func=cmd_tag_filter)
