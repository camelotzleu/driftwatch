"""Command registry for DriftWatch CLI."""
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
)

ALL_COMMANDS = [
    baseline_cmd,
    schedule_cmd,
    notify_cmd,
    summarize_cmd,
    history_cmd,
    tagger_cmd,
    pruner_cmd,
    alert_cmd,
    compare_cmd,
]


def register_all(subparsers) -> None:
    """Register every command module with *subparsers*."""
    for mod in ALL_COMMANDS:
        mod.register(subparsers)
