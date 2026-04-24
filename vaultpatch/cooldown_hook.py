"""Cooldown hook: integrate cooldown checks into the CLI apply flow."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Optional

import click

from vaultpatch.cooldown import CooldownStore

_DEFAULT_STORE_PATH = Path(".vaultpatch") / "cooldown.json"


def load_store(store_path: Optional[Path] = None) -> CooldownStore:
    path = store_path or _DEFAULT_STORE_PATH
    return CooldownStore.load(path)


def save_store(store: CooldownStore, store_path: Optional[Path] = None) -> None:
    path = store_path or _DEFAULT_STORE_PATH
    store.save(path)


def check_cooldowns(
    namespace: str,
    paths: List[str],
    store: CooldownStore,
    dry_run: bool = False,
) -> List[str]:
    """Return list of paths currently blocked by an active cooldown."""
    blocked = [p for p in paths if store.is_blocked(namespace, p)]
    if blocked:
        for path in blocked:
            entry = store.get(namespace, path)
            expires = entry.expires_at().isoformat() if entry else "unknown"
            msg = f"[cooldown] {namespace}:{path} is blocked until {expires}"
            if dry_run:
                click.echo(msg)
            else:
                click.echo(msg, err=True)
    return blocked


def abort_on_cooldown(blocked_paths: List[str], dry_run: bool = False) -> None:
    if blocked_paths and not dry_run:
        click.echo(
            f"Apply aborted: {len(blocked_paths)} path(s) under cooldown.", err=True
        )
        sys.exit(1)


def record_applied(
    namespace: str,
    paths: List[str],
    store: CooldownStore,
    cooldown_seconds: int = 300,
) -> None:
    """Record that paths were successfully applied, starting their cooldown."""
    for path in paths:
        store.record(namespace, path, cooldown_seconds=cooldown_seconds)
