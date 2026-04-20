"""CLI sub-command: vaultpatch drift."""
from __future__ import annotations

import click

from vaultpatch.config import VaultPatchConfig
from vaultpatch.drift import detect_drift
from vaultpatch.drift_hook import abort_on_drift, echo_drift_results
from vaultpatch.fetch import fetch_secrets


@click.command("drift")
@click.option(
    "--snapshot-dir",
    default=".vaultpatch_snapshots",
    show_default=True,
    help="Directory containing saved snapshots.",
)
@click.option(
    "--namespace",
    default=None,
    help="Limit drift check to a single namespace.",
)
@click.option("--verbose", "-v", is_flag=True, default=False)
@click.option(
    "--fail-on-drift",
    is_flag=True,
    default=False,
    help="Exit with code 1 if drift is detected.",
)
@click.pass_context
def drift_cmd(ctx: click.Context, snapshot_dir: str, namespace, verbose: bool, fail_on_drift: bool) -> None:
    """Compare live secrets against saved snapshots and report drift."""
    cfg: VaultPatchConfig = ctx.obj["config"]

    namespaces = (
        [cfg.get_namespace(namespace)] if namespace else cfg.namespaces
    )

    all_results = []
    for ns in namespaces:
        fetch_result = fetch_secrets(ns)
        results = detect_drift(fetch_result, snapshot_dir, ns.name)
        all_results.extend(results)

    echo_drift_results(all_results, verbose=verbose)

    if fail_on_drift:
        abort_on_drift(all_results)
