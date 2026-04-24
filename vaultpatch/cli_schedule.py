"""CLI sub-command: `vaultpatch schedule check` — inspect the current schedule status."""
from __future__ import annotations

from datetime import datetime, timezone

import click

from vaultpatch.config import VaultPatchConfig
from vaultpatch.schedule import check_schedule, windows_from_config
from vaultpatch.schedule_hook import echo_schedule_status


@click.group("schedule")
def schedule_cmd() -> None:  # pragma: no cover
    """Inspect or enforce patch scheduling windows."""


def _parse_at(at_str: str) -> datetime:
    """Parse an ISO-8601 datetime string into a timezone-aware datetime.

    Accepts strings ending in 'Z' as a shorthand for UTC (+00:00).

    Raises:
        click.BadParameter: If the string cannot be parsed as ISO-8601.
    """
    try:
        return datetime.fromisoformat(at_str.replace("Z", "+00:00"))
    except ValueError:
        raise click.BadParameter(
            f"{at_str!r} is not a valid ISO-8601 datetime.",
            param_hint="'--at'",
        )


@schedule_cmd.command("check")
@click.option("--config", "config_path", default="vaultpatch.yaml", show_default=True)
@click.option(
    "--at",
    "at_str",
    default=None,
    help="ISO-8601 datetime to evaluate instead of now (e.g. 2024-01-08T10:00:00Z).",
)
def check_cmd(config_path: str, at_str: str | None) -> None:
    """Check whether the current time (or --at) falls inside a permitted window."""
    cfg = VaultPatchConfig.from_file(config_path)
    raw_windows = getattr(cfg, "schedule_windows", []) or []
    windows = windows_from_config(raw_windows)

    at: datetime = _parse_at(at_str) if at_str else datetime.now(timezone.utc)

    result = check_schedule(windows, at=at)
    echo_schedule_status(result)

    if result.blocked:
        raise SystemExit(1)
