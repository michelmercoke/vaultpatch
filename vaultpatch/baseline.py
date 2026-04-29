"""Baseline snapshot management for drift detection anchoring."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

BASELINE_VERSION = 1


@dataclass
class BaselineEntry:
    namespace: str
    path: str
    secrets: Dict[str, str]
    captured_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    label: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "namespace": self.namespace,
            "path": self.path,
            "secrets": self.secrets,
            "captured_at": self.captured_at,
            "label": self.label,
        }


@dataclass
class BaselineStore:
    _entries: Dict[str, BaselineEntry] = field(default_factory=dict)

    def _key(self, namespace: str, path: str) -> str:
        return f"{namespace}::{path}"

    def set(self, entry: BaselineEntry) -> None:
        self._entries[self._key(entry.namespace, entry.path)] = entry

    def get(self, namespace: str, path: str) -> Optional[BaselineEntry]:
        return self._entries.get(self._key(namespace, path))

    def all(self) -> List[BaselineEntry]:
        return list(self._entries.values())

    def remove(self, namespace: str, path: str) -> bool:
        key = self._key(namespace, path)
        if key in self._entries:
            del self._entries[key]
            return True
        return False


def save_baseline(store: BaselineStore, path: Path) -> None:
    data = {
        "version": BASELINE_VERSION,
        "entries": [e.to_dict() for e in store.all()],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


def load_baseline(path: Path) -> BaselineStore:
    if not path.exists():
        raise FileNotFoundError(f"Baseline file not found: {path}")
    data = json.loads(path.read_text())
    if data.get("version") != BASELINE_VERSION:
        raise ValueError(f"Unsupported baseline version: {data.get('version')}")
    store = BaselineStore()
    for item in data.get("entries", []):
        store.set(BaselineEntry(
            namespace=item["namespace"],
            path=item["path"],
            secrets=item["secrets"],
            captured_at=item["captured_at"],
            label=item.get("label"),
        ))
    return store


def baseline_key(namespace: str, path: str) -> str:
    return f"{namespace}::{path}"
