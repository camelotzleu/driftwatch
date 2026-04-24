"""Register all CLI sub-commands."""
from driftwatch.commands import (
    alert_cmd,
    annotate_cmd,
    audit_cmd,
    baseline_cmd,
    baseline_diff_cmd,
    classify_cmd,
    compare_cmd,
    correlate_cmd,
    deduplicate_cmd,
    export_cmd,
    frequency_cmd,
    group_cmd,
    history_cmd,
    ignore_cmd,
    notify_cmd,
    pin_cmd,
    pruner_cmd,
    rank_cmd,
    resolve_cmd,
    schedule_cmd,
    score_cmd,
    silence_cmd,
    snapshot_diff_cmd,
    summarize_cmd,
    suppress_cmd,
    tagger_cmd,
    trend_cmd,
    validate_cmd,
    watchlist_cmd,
)


def register_all(subparsers) -> None:
    """Attach every command module to the top-level argument parser."""
    for mod in [
        alert_cmd, annotate_cmd, audit_cmd, baseline_cmd, baseline_diff_cmd,
        classify_cmd, compare_cmd, correlate_cmd, deduplicate_cmd, export_cmd,
        frequency_cmd, group_cmd, history_cmd, ignore_cmd, notify_cmd,
        pin_cmd, pruner_cmd, rank_cmd, resolve_cmd, schedule_cmd, score_cmd,
        silence_cmd, snapshot_diff_cmd, summarize_cmd, suppress_cmd,
        tagger_cmd, trend_cmd, validate_cmd, watchlist_cmd,
    ]:
        mod.register(subparsers)
