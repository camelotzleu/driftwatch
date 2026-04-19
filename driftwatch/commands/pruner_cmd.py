"""CLI commands for pruning history and stale baselines."""

from __future__ import annotations

import argparse

from driftwatch.pruner import (
    prune_history_by_age,
    prune_history_by_count,
    prune_baseline_if_stale,
)


def cmd_prune_history(args: argparse.Namespace) -> None:
    cfg_path = getattr(args, "config_dir", ".")
    removed = 0
    if args.max_age_days is not None:
        removed += prune_history_by_age(args.max_age_days, cfg_path)
    if args.max_entries is not None:
        removed += prune_history_by_count(args.max_entries, cfg_path)
    if removed:
        print(f"Pruned {removed} history entry/entries.")
    else:
        print("Nothing to prune.")


def cmd_prune_baseline(args: argparse.Namespace) -> None:
    cfg_path = getattr(args, "config_dir", ".")
    removed = prune_baseline_if_stale(args.max_age_days, cfg_path)
    if removed:
        print(f"Baseline removed (older than {args.max_age_days} days).")
    else:
        print("Baseline is current or does not exist.")


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p_hist = subparsers.add_parser("prune-history", help="Prune drift history entries")
    p_hist.add_argument("--max-age-days", type=int, default=None, help="Remove entries older than N days")
    p_hist.add_argument("--max-entries", type=int, default=None, help="Keep only the N most recent entries")
    p_hist.set_defaults(func=cmd_prune_history)

    p_base = subparsers.add_parser("prune-baseline", help="Remove stale baseline snapshot")
    p_base.add_argument("--max-age-days", type=int, required=True, help="Remove baseline if older than N days")
    p_base.set_defaults(func=cmd_prune_baseline)
