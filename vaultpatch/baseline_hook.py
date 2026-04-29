"""Hook functions for baseline capture and comparison in CLI flows."""
from __future__ import annotations

import click
from pathlib import Path
from typing import Dict, List, Optional

from vaultpatch.baseline import BaselineEntry, BaselineStore, load_baseline, save_baseline
from vaultpatch.fetch import FetchResult


def capture_baseline(
    fetch_results: Dict[str, FetchResult],
    namespace: str,
    label: Optional[str] = None,
) -> BaselineStore:
    """Build a BaselineStore from fetch results for a given namespace."""
    store = BaselineStore()
    for path, result in fetch_results.items():
        if result.success:
            store.set(BaselineEntry(
                namespace=namespace,
                path=path,
                secrets=dict(result.secrets),
                label=label,
            ))
    return store


def merge_into_store(
    existing: BaselineStore,
    incoming: BaselineStore,
) -> BaselineStore:
    """Overlay incoming entries onto existing store, returning updated store."""
    for entry in incoming.all():
        existing.set(entry)
    return existing


def echo_baseline_summary(store: BaselineStore, verbose: bool = False) -> None:
    entries = store.all()
    click.echo(f"Baseline contains {len(entries)} path(s).")
    if verbose:
        for e in sorted(entries, key=lambda x: (x.namespace, x.path)):
            label_str = f" [{e.label}]" if e.label else ""
            click.echo(f"  {e.namespace}/{e.path}{label_str} — {len(e.secrets)} key(s) @ {e.captured_at}")


def load_or_empty(baseline_path: Path) -> BaselineStore:
    """Load baseline from file, returning empty store if file does not exist."""
    try:
        return load_baseline(baseline_path)
    except FileNotFoundError:
        return BaselineStore()
