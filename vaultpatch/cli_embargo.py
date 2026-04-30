"""CLI subcommand for embargo management."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

import click

from vaultpatch.embargo import EmbargoConfig, EmbargoWindow
from vaultpatch.embargo_hook import abort_on_embargo, echo_embargo_results, run_embargo_check


@click.group("embargo")
def embargo_cmd() -> None:
    """Manage and check path embargo windows."""


@embargo_cmd.command("check")
@click.argument("paths", nargs=-1, required=True)
@click.option("--label", default="", help="Embargo label")
@click.option("--path-pattern", required=True, help="Path pattern (glob-style)")
@click.option("--start", required=True, help="Embargo start (ISO-8601)")
@click.option("--end", required=True, help="Embargo end (ISO-8601)")
@click.option("--dry-run", is_flag=True, default=False)
@click.option("--at", "at_time", default=None, help="Override current time (ISO-8601)")
def check_cmd(
    paths: tuple,
    label: str,
    path_pattern: str,
    start: str,
    end: str,
    dry_run: bool,
    at_time: Optional[str],
) -> None:
    """Check whether PATHS fall under an active embargo window."""
    now: Optional[datetime] = None
    if at_time:
        now = datetime.fromisoformat(at_time)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

    window = EmbargoWindow(label=label, path_pattern=path_pattern, start=start, end=end)
    config = EmbargoConfig(windows=[window])
    result = run_embargo_check(list(paths), config, now=now)
    echo_embargo_results(result)
    if not dry_run:
        abort_on_embargo(result)
