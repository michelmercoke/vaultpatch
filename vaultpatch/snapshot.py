"""Snapshot: persist and load secret state for rollback."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

SNAPSHOT_VERSION = 1


def save_snapshot(path: Path, data: Dict[str, Dict[str, str]]) -> None:
    """Persist a namespace->path->secrets mapping to disk."""
    payload = {"version": SNAPSHOT_VERSION, "secrets": data}
    path.write_text(json.dumps(payload, indent=2))


def load_snapshot(path: Path) -> Dict[str, Dict[str, str]]:
    """Load a previously saved snapshot. Returns secrets mapping."""
    if not path.exists():
        raise FileNotFoundError(f"Snapshot not found: {path}")
    raw = json.loads(path.read_text())
    if raw.get("version") != SNAPSHOT_VERSION:
        raise ValueError(f"Unsupported snapshot version: {raw.get('version')}")
    return raw["secrets"]


def snapshot_key(namespace: str, secret_path: str) -> str:
    """Canonical key used inside a snapshot dict."""
    return f"{namespace}/{secret_path}"
