"""CLI hook for dependency resolution.

Integrates with the apply pipeline to reorder paths and surface warnings.
"""
from __future__ import annotations

from typing import Dict, List

import click

from vaultpatch.dependency import DependencyResult, resolve_dependencies


def apply_dependency_order(
    paths: List[str],
    deps: Dict[str, List[str]],
    dry_run: bool = False,
) -> DependencyResult:
    """Resolve dependency order and return the result for further processing."""
    result = resolve_dependencies(paths, deps)
    return result


def echo_dependency_results(result: DependencyResult) -> None:
    """Print ordering and any violations to stdout/stderr."""
    if result.has_violations:
        for v in result.violations:
            click.echo(f"[dependency] WARNING: {v}", err=True)

    click.echo("[dependency] apply order:")
    for i, path in enumerate(result.ordered, 1):
        click.echo(f"  {i:>3}. {path}")


def abort_on_cycle(result: DependencyResult) -> None:
    """Raise SystemExit if a circular dependency was detected."""
    for v in result.violations:
        if "circular" in v.reason:
            raise SystemExit(
                f"[dependency] Aborting: {v.reason}. "
                "Fix the cycle before applying."
            )
