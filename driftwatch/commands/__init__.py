"""Register all CLI sub-commands."""
from __future__ import annotations
import argparse


def register_all(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    from driftwatch.commands import baseline_cmd
    from driftwatch.commands import schedule_cmd
    from driftwatch.commands import notify_cmd
    from driftwatch.commands import summarize_cmd
    from driftwatch.commands import history_cmd
    from driftwatch.commands import tagger_cmd
    from driftwatch.commands import pruner_cmd
    from driftwatch.commands import alert_cmd
    from driftwatch.commands import export_cmd
    from driftwatch.commands import compare_cmd
    from driftwatch.commands import score_cmd
    from driftwatch.commands import audit_cmd
    from driftwatch.commands import suppress_cmd
    from driftwatch.commands import frequency_cmd
    from driftwatch.commands import group_cmd
    from driftwatch.commands import trend_cmd
    from driftwatch.commands import classify_cmd
    from driftwatch.commands import annotate_cmd
    from driftwatch.commands import rank_cmd
    from driftwatch.commands import correlate_cmd
    from driftwatch.commands import baseline_diff_cmd
    from driftwatch.commands import deduplicate_cmd
    from driftwatch.commands import snapshot_diff_cmd

    for mod in [
        baseline_cmd, schedule_cmd, notify_cmd, summarize_cmd, history_cmd,
        tagger_cmd, pruner_cmd, alert_cmd, export_cmd, compare_cmd, score_cmd,
        audit_cmd, suppress_cmd, frequency_cmd, group_cmd, trend_cmd,
        classify_cmd, annotate_cmd, rank_cmd, correlate_cmd, baseline_diff_cmd,
        deduplicate_cmd, snapshot_diff_cmd,
    ]:
        mod.register(sub)
