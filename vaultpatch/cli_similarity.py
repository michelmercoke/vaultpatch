"""CLI sub-commands for the similarity feature."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import click

from vaultpatch.similarity import SimilarityConfig
from vaultpatch.similarity_hook import (
    abort_on_similarity_failure,
    echo_similarity_results,
    run_similarity_check,
)


@click.group("similarity")
def similarity_cmd() -> None:
    """Commands for cross-namespace secret similarity detection."""


@similarity_cmd.command("check")
@click.argument("secrets_file", type=click.Path(exists=True))
@click.option(
    "--threshold",
    default=0.85,
    show_default=True,
    help="Similarity ratio threshold (0.0-1.0).",
)
@click.option(
    "--ignore-key",
    "ignore_keys",
    multiple=True,
    help="Secret keys to exclude from comparison.",
)
@click.option(
    "--fail/--no-fail",
    default=True,
    show_default=True,
    help="Exit non-zero when violations are found.",
)
def check_cmd(
    secrets_file: str,
    threshold: float,
    ignore_keys: tuple,
    fail: bool,
) -> None:
    """Check a JSON file of secrets for near-duplicate values.

    SECRETS_FILE should be a JSON object mapping path -> {key: value}.
    """
    raw = json.loads(Path(secrets_file).read_text())
    cfg = SimilarityConfig(threshold=threshold, ignore_keys=list(ignore_keys))
    result = run_similarity_check(raw, cfg)
    echo_similarity_results(result)
    if fail:
        abort_on_similarity_failure(result)
