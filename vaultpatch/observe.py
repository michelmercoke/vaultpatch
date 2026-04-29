"""Observe module: track and report on secret change frequency per path."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class ObserveEntry:
    path: str
    namespace: str
    change_count: int
    first_seen: str
    last_seen: str
    keys_changed: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "namespace": self.namespace,
            "change_count": self.change_count,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "keys_changed": sorted(set(self.keys_changed)),
        }


@dataclass
class ObserveStore:
    _entries: Dict[str, ObserveEntry] = field(default_factory=dict)

    def record(self, path: str, namespace: str, keys: List[str]) -> ObserveEntry:
        now = _now_iso()
        if path in self._entries:
            entry = self._entries[path]
            entry.change_count += 1
            entry.last_seen = now
            entry.keys_changed.extend(keys)
        else:
            entry = ObserveEntry(
                path=path,
                namespace=namespace,
                change_count=1,
                first_seen=now,
                last_seen=now,
                keys_changed=list(keys),
            )
            self._entries[path] = entry
        return entry

    def get(self, path: str) -> Optional[ObserveEntry]:
        return self._entries.get(path)

    def all_entries(self) -> List[ObserveEntry]:
        return list(self._entries.values())

    def hotspots(self, top_n: int = 5) -> List[ObserveEntry]:
        return sorted(self._entries.values(), key=lambda e: e.change_count, reverse=True)[:top_n]

    def to_dict(self) -> dict:
        return {k: v.to_dict() for k, v in self._entries.items()}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_store(path: Path) -> ObserveStore:
    store = ObserveStore()
    if not path.exists():
        return store
    data = json.loads(path.read_text())
    for key, val in data.items():
        store._entries[key] = ObserveEntry(**val)
    return store


def save_store(store: ObserveStore, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(store.to_dict(), indent=2))
