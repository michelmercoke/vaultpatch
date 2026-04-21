"""Checkpoint support: tag a named point-in-time snapshot across namespaces."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

CHECKPOINT_VERSION = 1


@dataclass
class CheckpointEntry:
    namespace: str
    path: str
    secrets: Dict[str, str]

    def to_dict(self) -> dict:
        return {"namespace": self.namespace, "path": self.path, "secrets": self.secrets}


@dataclass
class Checkpoint:
    name: str
    created_at: str
    entries: List[CheckpointEntry] = field(default_factory=list)
    version: int = CHECKPOINT_VERSION

    def add(self, entry: CheckpointEntry) -> None:
        self.entries.append(entry)

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "name": self.name,
            "created_at": self.created_at,
            "entries": [e.to_dict() for e in self.entries],
        }


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def create_checkpoint(name: str) -> Checkpoint:
    """Create a new empty checkpoint with the given name."""
    return Checkpoint(name=name, created_at=_now_iso())


def save_checkpoint(checkpoint: Checkpoint, directory: str) -> Path:
    """Persist a checkpoint to *directory* as ``<name>.checkpoint.json``."""
    dest = Path(directory)
    dest.mkdir(parents=True, exist_ok=True)
    fp = dest / f"{checkpoint.name}.checkpoint.json"
    fp.write_text(json.dumps(checkpoint.to_dict(), indent=2))
    return fp


def load_checkpoint(name: str, directory: str) -> Checkpoint:
    """Load a previously saved checkpoint by name from *directory*."""
    fp = Path(directory) / f"{name}.checkpoint.json"
    if not fp.exists():
        raise FileNotFoundError(f"Checkpoint '{name}' not found in {directory}")
    data = json.loads(fp.read_text())
    if data.get("version") != CHECKPOINT_VERSION:
        raise ValueError(
            f"Unsupported checkpoint version: {data.get('version')}"
        )
    entries = [
        CheckpointEntry(
            namespace=e["namespace"], path=e["path"], secrets=e["secrets"]
        )
        for e in data.get("entries", [])
    ]
    return Checkpoint(
        name=data["name"],
        created_at=data["created_at"],
        entries=entries,
        version=data["version"],
    )


def list_checkpoints(directory: str) -> List[str]:
    """Return sorted names of all checkpoints stored in *directory*."""
    base = Path(directory)
    if not base.exists():
        return []
    return sorted(
        p.name.replace(".checkpoint.json", "")
        for p in base.glob("*.checkpoint.json")
    )
