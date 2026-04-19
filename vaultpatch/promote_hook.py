"""CLI hook for the promote feature."""
from typing import List

import click

from vaultpatch.config import VaultPatchConfig
from vaultpatch.promote import PromoteResult, promote_paths


def run_promote(
    cfg: VaultPatchConfig,
    source: str,
    target: str,
    paths: List[str],
    dry_run: bool = False,
) -> List[PromoteResult]:
    src_cfg = cfg.get_namespace(source)
    tgt_cfg = cfg.get_namespace(target)
    return promote_paths(src_cfg, tgt_cfg, paths, dry_run=dry_run)


def echo_promote_results(results: List[PromoteResult], dry_run: bool = False) -> None:
    prefix = "[dry-run] " if dry_run else ""
    ok = 0
    fail = 0
    for r in results:
        if r.success:
            click.echo(f"{prefix}✔  {r.path}  ({r.source} → {r.target})")
            ok += 1
        else:
            click.echo(
                click.style(
                    f"✖  {r.path}  ({r.source} → {r.target}): {r.error}",
                    fg="red",
                )
            )
            fail += 1
    click.echo(f"\nPromoted {ok} path(s), {fail} failure(s).")
