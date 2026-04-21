"""CLI commands for checkpoint management."""
from __future__ import annotations

import click

from vaultpatch.checkpoint import (
    create_checkpoint,
    save_checkpoint,
    load_checkpoint,
    list_checkpoints,
    CheckpointEntry,
)
from vaultpatch.config import VaultPatchConfig
from vaultpatch.fetch import fetch_secrets

DEFAULT_DIR = ".vaultpatch/checkpoints"


@click.group("checkpoint")
def checkpoint_cmd() -> None:  # pragma: no cover
    """Create, list and inspect named checkpoints."""


@checkpoint_cmd.command("create")
@click.argument("name")
@click.option("--config", "cfg_path", default="vaultpatch.yaml", show_default=True)
@click.option("--dir", "cp_dir", default=DEFAULT_DIR, show_default=True)
def create_cmd(name: str, cfg_path: str, cp_dir: str) -> None:
    """Snapshot current secrets into a named checkpoint."""
    cfg = VaultPatchConfig.from_file(cfg_path)
    cp = create_checkpoint(name)
    for ns_name, ns_cfg in cfg.namespaces.items():
        for path in ns_cfg.paths:
            result = fetch_secrets(ns_cfg, path)
            if result.success:
                cp.add(CheckpointEntry(namespace=ns_name, path=path, secrets=result.secrets))
            else:
                click.echo(f"[warn] {ns_name}:{path} — {result.error}", err=True)
    fp = save_checkpoint(cp, cp_dir)
    total = len(cp.entries)
    click.echo(f"Checkpoint '{name}' saved → {fp}  ({total} path(s))")


@checkpoint_cmd.command("list")
@click.option("--dir", "cp_dir", default=DEFAULT_DIR, show_default=True)
def list_cmd(cp_dir: str) -> None:
    """List all available checkpoints."""
    names = list_checkpoints(cp_dir)
    if not names:
        click.echo("No checkpoints found.")
        return
    for n in names:
        click.echo(n)


@checkpoint_cmd.command("show")
@click.argument("name")
@click.option("--dir", "cp_dir", default=DEFAULT_DIR, show_default=True)
def show_cmd(name: str, cp_dir: str) -> None:
    """Show the contents of a checkpoint."""
    try:
        cp = load_checkpoint(name, cp_dir)
    except FileNotFoundError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(f"Checkpoint : {cp.name}")
    click.echo(f"Created at : {cp.created_at}")
    click.echo(f"Entries    : {len(cp.entries)}")
    for entry in cp.entries:
        keys = ", ".join(sorted(entry.secrets.keys()))
        click.echo(f"  [{entry.namespace}] {entry.path}  keys=({keys})")
