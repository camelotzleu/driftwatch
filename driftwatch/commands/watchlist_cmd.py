"""CLI command: driftwatch watchlist — check drift against a resource watchlist."""
from __future__ import annotations

import argparse
import json
import sys

from driftwatch.collectors import get_collector
from driftwatch.comparator import compare_to_baseline
from driftwatch.config import DriftWatchConfig
from driftwatch.differ_watchlist import check_watchlist, watchlist_from_dicts
from driftwatch.reporter import render


def cmd_watchlist(args: argparse.Namespace, cfg: DriftWatchConfig) -> int:
    provider_cfg = next(
        (p for p in cfg.providers if p.name == args.provider), None
    )
    if provider_cfg is None:
        print(f"[error] unknown provider: {args.provider}", file=sys.stderr)
        return 1

    watchlist_raw: list = getattr(cfg, "watchlist", []) or []
    if not watchlist_raw:
        print("[warn] no watchlist entries configured", file=sys.stderr)
        return 1

    watchlist = watchlist_from_dicts(watchlist_raw)

    collector = get_collector(provider_cfg)
    snapshot = collector.collect()

    compare_result = compare_to_baseline(snapshot, provider_cfg.name)
    if compare_result.report is None:
        print("[error] no baseline found — run 'driftwatch baseline save' first",
              file=sys.stderr)
        return 1

    wl_report = check_watchlist(compare_result.report, watchlist)

    if args.format == "json":
        print(json.dumps(wl_report.to_dict(), indent=2))
    else:
        if not wl_report.watched:
            print("No watched resources found in drift.")
        else:
            print(f"Watched resources with drift ({wl_report.watched_hits} hit(s)):")
            for we in wl_report.watched:
                reason = f" [{we.reason}]" if we.reason else ""
                print(f"  {we.entry.resource_id} ({we.entry.change_type}){reason}")

    return 0 if not wl_report.watched else 2


def register(subparsers) -> None:
    p = subparsers.add_parser(
        "watchlist", help="check drift entries against a resource watchlist"
    )
    p.add_argument("provider", help="provider name to collect from")
    p.add_argument(
        "--format", choices=["text", "json"], default="text", help="output format"
    )
    p.set_defaults(func=cmd_watchlist)
