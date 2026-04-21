"""Lineage tracking: record which namespace a secret was promoted from."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

_LINEAGE_VERSION = 1


@dataclass
class LineageEntry:
    path: str
    source_namespace: str
    target_namespace: str
    promoted_at: str
    promoted_by: str

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "source_namespace": self.source_namespace,
            "target_namespace": self.target_namespace,
            "promoted_at": self.promoted_at,
            "promoted_by": self.promoted_by,
        }


@dataclass
class LineageRecord:
    version: int = _LINEAGE_VERSION
    entries: List[LineageEntry] = field(default_factory=list)

    def add(self, entry: LineageEntry) -> None:
        self.entries.append(entry)

    def for_path(self, path: str) -> List[LineageEntry]:
        return [e for e in self.entries if e.path == path]

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "entries": [e.to_dict() for e in self.entries],
        }


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def build_entry(
    path: str,
    source_namespace: str,
    target_namespace: str,
    promoted_by: Optional[str] = None,
) -> LineageEntry:
    actor = promoted_by or os.environ.get("USER", "unknown")
    return LineageEntry(
        path=path,
        source_namespace=source_namespace,
        target_namespace=target_namespace,
        promoted_at=_now_iso(),
        promoted_by=actor,
    )


def save_lineage(record: LineageRecord, filepath: Path) -> None:
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text(json.dumps(record.to_dict(), indent=2))


def load_lineage(filepath: Path) -> LineageRecord:
    if not filepath.exists():
        return LineageRecord()
    data = json.loads(filepath.read_text())
    if data.get("version") != _LINEAGE_VERSION:
        raise ValueError(
            f"Unsupported lineage version: {data.get('version')}"
        )
    entries = [
        LineageEntry(
            path=e["path"],
            source_namespace=e["source_namespace"],
            target_namespace=e["target_namespace"],
            promoted_at=e["promoted_at"],
            promoted_by=e["promoted_by"],
        )
        for e in data.get("entries", [])
    ]
    return LineageRecord(version=_LINEAGE_VERSION, entries=entries)
