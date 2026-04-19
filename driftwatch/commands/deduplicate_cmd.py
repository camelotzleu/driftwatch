"""CLI command: deduplicate drift entries from baseline comparison."""
from __future__ import annotations
import argparse
import json
from driftwatch.config import load as load_config
from driftwatch.collectors import get_collector
from driftwatch.baseline import load as load_baseline
from driftwatch.comparator import compare_snapshots
from driftwatch.differ_deduplicator import deduplicate_reports
from driftwatch.reporter import render


def cmd_deduplicate(args: argparse.Namespace) -> int:
    cfg = load_config(getattr(args, "config", None))
    baseline = load_baseline(cfg)
    if baseline is None:
        print("[error] No baseline found. Run 'baseline save' first.")
        return 1

    reports = []
    for provider_cfg in cfg.providers:
        collector = get_collector(provider_cfg)
        if collector is None:
            print(f"[warn] Unknown provider: {provider_cfg.name}")
            continue
        snapshot = collector.collect()
        report = compare_snapshots(baseline, snapshot)
        reports.append(report)

    result = deduplicate_reports(reports)

    fmt = getattr(args, "format", "text")
    if fmt == "json":
        print(json.dumps(result.to_dict(), indent=2))
    else:
        from driftwatch.differ import DriftReport
        merged = DriftReport(entries=result.entries)
        print(render(merged, fmt="text"))
        print(f"\nDuplicates removed: {result.duplicate_count}")
    return 0


def register(subparsers) -> None:
    p = subparsers.add_parser("deduplicate", help="Deduplicate drift entries across providers")
    p.add_argument("--config", default=None, help="Path to config file")
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.set_defaults(func=cmd_deduplicate)
