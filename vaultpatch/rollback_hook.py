"""CLI-facing helpers that wire snapshot + rollback together."""
from __future__ import annotations

from pathlib import Path
from typing import List

import click

from vaultpatch.config import VaultPatchConfig
from vaultpatch.rollback import RollbackResult, rollback_path
from vaultpatch.snapshot import load_snapshot, snapshot_key


def run_rollback(
    cfg: VaultPatchConfig, snapshot_file: Path
) -> List[RollbackResult]:
    """For every namespace+path in cfg, revert to snapshot values."""
    snapshots = load_snapshot(snapshot_file)
    results: List[RollbackResult] = []
    for ns in cfg.namespaces:
        for secret_path in ns.paths:
            key = snapshot_key(ns.name, secret_path)
            if key not in snapshots:
                click.echo(f"[skip] no snapshot for {key}", err=True)
                continue
            result = rollback_path(ns, secret_path, snapshots[key])
            results.append(result)
    return results


def echo_rollback_results(results: List[RollbackResult]) -> None:
    for r in results:
        if r.success:
            keys = ", ".join(r.reverted_keys) if r.reverted_keys else "(no changes)"
            click.echo(f"[ok]  {r.namespace}/{r.path}  reverted: {keys}")
        else:
            click.echo(f"[err] {r.namespace}/{r.path}  {r.error}", err=True)
