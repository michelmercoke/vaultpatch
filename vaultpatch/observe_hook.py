"""Observe hook: integrates ObserveStore with diff results in the CLI pipeline."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import click

from vaultpatch.diff import SecretDiff
from vaultpatch.observe import ObserveStore, load_store, save_store

_DEFAULT_STORE = Path(".vaultpatch") / "observe.json"


def record_observations(
    diffs_by_path: Dict[str, List[SecretDiff]],
    namespace: str,
    store_path: Path = _DEFAULT_STORE,
) -> ObserveStore:
    """Record all changed/added/removed keys per path into the observe store."""
    store = load_store(store_path)
    for path, diffs in diffs_by_path.items():
        changed_keys = [
            d.key for d in diffs if d.is_changed() or d.is_added() or d.is_removed()
        ]
        if changed_keys:
            store.record(path=path, namespace=namespace, keys=changed_keys)
    save_store(store, store_path)
    return store


def echo_hotspots(store: ObserveStore, top_n: int = 5) -> None:
    """Print the most frequently changed paths to stdout."""
    hotspots = store.hotspots(top_n=top_n)
    if not hotspots:
        click.echo("No observations recorded yet.")
        return
    click.echo(f"Top {len(hotspots)} most-changed paths:")
    for entry in hotspots:
        click.echo(
            f"  {entry.path}  [{entry.namespace}]  "
            f"changes={entry.change_count}  last={entry.last_seen}"
        )


def echo_all_observations(store: ObserveStore) -> None:
    """Print all observed paths."""
    entries = store.all_entries()
    if not entries:
        click.echo("No observations recorded.")
        return
    for entry in sorted(entries, key=lambda e: e.path):
        keys_preview = ", ".join(sorted(set(entry.keys_changed))[:5])
        click.echo(
            f"  {entry.path}: {entry.change_count} change(s)  keys=[{keys_preview}]"
        )
