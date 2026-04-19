"""CLI command: rank drift entries by impact."""
from __future__ import annotations
import argparse
import json
from driftwatch.config import load as load_config
from driftwatch.collectors import get_collector
from driftwatch.baseline import load as load_baseline
from driftwatch.differ import diff
from driftwatch.differ_ranker import rank_report


def cmd_rank(args: argparse.Namespace) -> int:
    cfg = load_config()
    provider_cfg = next(
        (p for p in cfg.providers if p.name == args.provider), None
    )
    if provider_cfg is None:
        print(f"Unknown provider: {args.provider}")
        return 1

    baseline = load_baseline(args.provider)
    if baseline is None:
        print("No baseline found. Run 'driftwatch baseline save' first.")
        return 1

    collector = get_collector(provider_cfg)
    current = collector.collect()
    report = diff(baseline, current)

    top_n = getattr(args, "top", 0)
    ranked = rank_report(report, top_n=top_n)

    if args.format == "json":
        print(json.dumps(ranked.to_dict(), indent=2))
    else:
        if not ranked.ranked:
            print("No drift entries to rank.")
            return 0
        print(f"{'SCORE':>6}  {'CHANGE':8}  {'KIND':16}  RESOURCE")
        print("-" * 60)
        for r in ranked.ranked:
            print(f"{r.score:>6.2f}  {r.entry.change_type:8}  {r.entry.kind:16}  {r.entry.resource_id}")
    return 0


def register(subparsers) -> None:
    p = subparsers.add_parser("rank", help="Rank drift entries by impact score")
    p.add_argument("provider", help="Provider name")
    p.add_argument("--top", type=int, default=0, help="Show top N entries (0 = all)")
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.set_defaults(func=cmd_rank)
