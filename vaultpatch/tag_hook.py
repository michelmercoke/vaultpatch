"""CLI-level helpers for tag operations used by cli_tag.py."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

import click

from vaultpatch.tag import TagStore, load_tags, save_tags

_DEFAULT_TAG_FILE = ".vaultpatch_tags.json"


def resolve_store(tag_file: Optional[str]) -> tuple[TagStore, Path]:
    """Load existing store or create a new empty one."""
    fp = Path(tag_file or _DEFAULT_TAG_FILE)
    if fp.exists():
        store = load_tags(fp)
    else:
        store = TagStore()
    return store, fp


def cmd_tag_set(namespace: str, path: str, tags: List[str], tag_file: Optional[str]) -> None:
    store, fp = resolve_store(tag_file)
    entry = store.set_tags(namespace, path, tags)
    save_tags(store, fp)
    click.echo(f"Tagged {namespace}::{path} → {', '.join(sorted(entry.tags))}")


def cmd_tag_list(tag: Optional[str], tag_file: Optional[str]) -> None:
    store, _ = resolve_store(tag_file)
    if tag:
        entries = store.find_by_tag(tag)
        click.echo(f"Paths tagged '{tag}':")
    else:
        entries = store.all_entries()
        click.echo("All tagged paths:")
    if not entries:
        click.echo("  (none)")
        return
    for e in entries:
        click.echo(f"  {e.namespace}::{e.path}  [{', '.join(sorted(e.tags))}]")


def cmd_tag_remove(namespace: str, path: str, tag: str, tag_file: Optional[str]) -> None:
    store, fp = resolve_store(tag_file)
    entry = store.get(namespace, path)
    if entry is None:
        click.echo(f"No tags found for {namespace}::{path}", err=True)
        return
    entry.remove_tag(tag)
    save_tags(store, fp)
    click.echo(f"Removed tag '{tag}' from {namespace}::{path}")
