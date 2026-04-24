"""CLI hook that enforces quota checks before applying patches."""
from __future__ import annotations

import sys
from typing import List

import click

from vaultpatch.diff import SecretDiff
from vaultpatch.quota import QuotaConfig, QuotaResult, check_quota


def run_quota_check(
    diffs_by_path: dict[str, List[SecretDiff]],
    config: QuotaConfig,
) -> QuotaResult:
    """Run quota check and return the result."""
    return check_quota(diffs_by_path, config)


def echo_quota_results(result: QuotaResult) -> None:
    """Print quota violations to stderr."""
    if not result.exceeded:
        click.echo("quota: all checks passed.", err=False)
        return
    for v in result.violations:
        click.echo(f"quota violation: {v}", err=True)


def abort_on_quota_exceeded(result: QuotaResult) -> None:
    """Abort the process if quota was exceeded."""
    if result.exceeded:
        click.echo(
            f"Aborting: {len(result.violations)} quota violation(s) detected.",
            err=True,
        )
        sys.exit(1)
