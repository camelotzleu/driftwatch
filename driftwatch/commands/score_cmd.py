"""CLI command: driftwatch score — show drift severity scores."""
from __future__ import annotations
import argparse
import json
from driftwatch.config import load as load_config
from driftwatch.collectors import get_collector
from driftwatch.baseline import load as load_baseline
from driftwatch.differ import diff_snapshots
from driftwatch.scorer import score_report


def cmd_score(args: argparse.Namespace) -> int:
    cfg = load_config(getattr(args, "config", None))
    provider = args.provider
    pcfg = cfg.providers.get(provider)
    if pcfg is None:
        print(f"[error] provider '{provider}' not found in config")
        return 1

    baseline = load_baseline(provider)
    if baseline is None:
        print(f"[error] no baseline for provider '{provider}'. Run 'baseline save' first.")
        return 1

    collector = get_collector(provider, pcfg)
    current = collector.collect()
    report = diff_snapshots(baseline, current)

    scored = score_report(report)
    if args.format == "json":
        print(json.dumps(scored.to_dict(), indent=2))
    else:
        if not scored.entries:
            print("No drift detected. Score: 0")
            return 0
        print(f"Total drift score: {scored.total_score:.2f}")
        print(f"{'Resource':<40} {'Kind':<10} {'Score':>6}")
        print("-" * 60)
        for se in scored.entries:
            print(f"{se.entry.resource_id:<40} {se.entry.kind:<10} {se.score:>6.2f}")
    return 0


def register(subparsers) -> None:
    p = subparsers.add_parser("score", help="Score drift severity for a provider")
    p.add_argument("provider", help="Provider name")
    p.add_argument("--config", default=None, help="Path to config file")
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.set_defaults(func=cmd_score)
