"""CLI-facing hooks for the similarity check feature."""
from __future__ import annotations

import sys
from typing import Dict, Optional

import click

from vaultpatch.similarity import SimilarityConfig, SimilarityResult, check_similarity


def run_similarity_check(
    secrets: Dict[str, Dict[str, str]],
    cfg: Optional[SimilarityConfig] = None,
) -> SimilarityResult:
    """Delegate to check_similarity and return the result."""
    return check_similarity(secrets, cfg)


def echo_similarity_results(result: SimilarityResult) -> None:
    """Print a human-readable summary of similarity violations."""
    if not result.has_violations:
        click.echo(f"similarity: ok (checked {result.checked} pairs)")
        return

    click.echo(
        f"similarity: {len(result.violations)} violation(s) "
        f"across {result.checked} pairs checked",
        err=True,
    )
    for v in result.violations:
        click.echo(f"  SIMILAR  {v}", err=True)


def abort_on_similarity_failure(result: SimilarityResult) -> None:
    """Raise SystemExit if any similarity violations were found."""
    if result.has_violations:
        click.echo(
            f"Aborting: {len(result.violations)} similarity violation(s) detected.",
            err=True,
        )
        sys.exit(1)
