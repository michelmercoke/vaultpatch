"""CLI commands for tagging secret paths."""

from __future__ import annotations

from typing import Optional

import click

from vaultpatch.tag_hook import cmd_tag_list, cmd_tag_remove, cmd_tag_set


@click.group("tag")
def tag_cmd() -> None:
    """Tag and query secret paths with metadata labels."""


@tag_cmd.command("set")
@click.argument("namespace")
@click.argument("path")
@click.argument("tags", nargs=-1, required=True)
@click.option("--tag-file", default=None, help="Path to tag store file.")
def set_cmd(namespace: str, path: str, tags: tuple, tag_file: Optional[str]) -> None:
    """Assign TAGS to a secret PATH in NAMESPACE."""
    cmd_tag_set(namespace, path, list(tags), tag_file)


@tag_cmd.command("list")
@click.option("--tag", default=None, help="Filter by a specific tag.")
@click.option("--tag-file", default=None, help="Path to tag store file.")
def list_cmd(tag: Optional[str], tag_file: Optional[str]) -> None:
    """List tagged paths, optionally filtered by TAG."""
    cmd_tag_list(tag, tag_file)


@tag_cmd.command("remove")
@click.argument("namespace")
@click.argument("path")
@click.argument("tag")
@click.option("--tag-file", default=None, help="Path to tag store file.")
def remove_cmd(namespace: str, path: str, tag: str, tag_file: Optional[str]) -> None:
    """Remove a TAG from a secret PATH in NAMESPACE."""
    cmd_tag_remove(namespace, path, tag, tag_file)
