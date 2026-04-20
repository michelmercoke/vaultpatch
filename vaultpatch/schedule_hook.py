"""CLI hook: enforce schedule windows before diff / apply runs."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, Sequence

import click

from vaultpatch.schedule import ScheduleResult, ScheduleWindow, check_schedule


def enforce_schedule(
    windows: Sequence[ScheduleWindow],
    at: Optional[datetime] = None,
    *,
    dry_run: bool = False,
) -> ScheduleResult:
    """Check schedule and abort the CLI if the run is not permitted.

    In *dry_run* mode the check is still performed and printed, but the
    process is never aborted.
    """
    if at is None:
        at = datetime.now(timezone.utc)

    result = check_schedule(windows, at=at)

    if result.allowed:
        click.echo(f"[schedule] ✓ {result.reason}")
    else:
        click.echo(f"[schedule] ✗ {result.reason}", err=True)
        if not dry_run:
            raise SystemExit(1)

    return result


def echo_schedule_status(result: ScheduleResult) -> None:
    """Print a human-readable one-liner for the schedule check result."""
    icon = "✓" if result.allowed else "✗"
    window_name = result.window.name if result.window else "–"
    click.echo(f"[schedule] {icon} window={window_name!r}  reason={result.reason!r}")
