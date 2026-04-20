"""CLI hook: wire drift detection into the vaultpatch command surface."""
from __future__ import annotations

import sys
from typing import List

import click

from vaultpatch.drift import DriftResult, summarise_drift


def echo_drift_results(results: List[DriftResult], verbose: bool = False) -> None:
    """Print drift results to stdout; errors go to stderr."""
    for r in results:
        if not r.success:
            click.echo(
                click.style(f"  ERROR [{r.namespace}] {r.path}: {r.error}", fg="red"),
                err=True,
            )
            continue

        if r.has_drift:
            click.echo(
                click.style(f"  DRIFT [{r.namespace}] {r.path}", fg="yellow")
            )
            if verbose:
                for d in r.diffs:
                    click.echo(f"    {d.label}: {d.key}")
        else:
            if verbose:
                click.echo(
                    click.style(f"  OK    [{r.namespace}] {r.path}", fg="green")
                )

    click.echo(summarise_drift(results))


def abort_on_drift(results: List[DriftResult]) -> None:
    """Exit with code 1 if any path has drifted or errored."""
    has_issues = any(not r.success or r.has_drift for r in results)
    if has_issues:
        click.echo(
            click.style("Drift detected — aborting.", fg="red"),
            err=True,
        )
        sys.exit(1)
