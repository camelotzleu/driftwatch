"""Register all CLI sub-commands."""
from __future__ import annotations

import argparse


def register_all(subparsers: argparse._SubParsersAction,
                 parent: argparse.ArgumentParser) -> None:
    from driftwatch.commands import (
        baseline_cmd,
        schedule_cmd,
        notify_cmd,
        summarize_cmd,
        history_cmd,
        tagger_cmd,
        pruner_cmd,
        alert_cmd,
        compare_cmd,
        export_cmd,
        audit_cmd,
    )

    baseline_cmd.register(subparsers, parent)
    schedule_cmd.register(subparsers, parent)
    notify_cmd.register(subparsers, parent)
    summarize_cmd.register(subparsers, parent)
    history_cmd.register(subparsers, parent)
    tagger_cmd.register(subparsers, parent)
    pruner_cmd.register(subparsers, parent)
    alert_cmd.register(subparsers, parent)
    compare_cmd.register(subparsers, parent)
    export_cmd.register(subparsers, parent)
    audit_cmd.register(subparsers, parent)
