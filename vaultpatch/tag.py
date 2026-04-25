"""Tag secrets paths with arbitrary metadata labels for grouping and filtering."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

TAG_FILE_VERSION = 1


@dataclass
class TagEntry:
    path: str
    namespace: str
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"path": self.path, "namespace": self.namespace, "tags": sorted(self.tags)}

    def has_tag(self, tag: str) -> bool:
        return tag in self.tags

    def add_tag(self, tag: str) -> None:
        if tag not in self.tags:
            self.tags.append(tag)

    def remove_tag(self, tag: str) -> None:
        self.tags = [t for t in self.tags if t != tag]


@dataclass
class TagStore:
    _entries: Dict[str, TagEntry] = field(default_factory=dict)

    def _key(self, namespace: str, path: str) -> str:
        return f"{namespace}::{path}"

    def set_tags(self, namespace: str, path: str, tags: List[str]) -> TagEntry:
        key = self._key(namespace, path)
        entry = TagEntry(path=path, namespace=namespace, tags=list(tags))
        self._entries[key] = entry
        return entry

    def get(self, namespace: str, path: str) -> Optional[TagEntry]:
        return self._entries.get(self._key(namespace, path))

    def find_by_tag(self, tag: str) -> List[TagEntry]:
        return [e for e in self._entries.values() if e.has_tag(tag)]

    def all_entries(self) -> List[TagEntry]:
        return list(self._entries.values())

    def all_tags(self) -> List[str]:
        """Return a sorted list of all unique tags across all entries."""
        return sorted({tag for entry in self._entries.values() for tag in entry.tags})

    def to_dict(self) -> dict:
        return {
            "version": TAG_FILE_VERSION,
            "entries": [e.to_dict() for e in self._entries.values()],
        }


def save_tags(store: TagStore, filepath: Path) -> None:
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text(json.dumps(store.to_dict(), indent=2))


def load_tags(filepath: Path) -> TagStore:
    if not filepath.exists():
        raise FileNotFoundError(f"Tag store not found: {filepath}")
    data = json.loads(filepath.read_text())
    if data.get("version") != TAG_FILE_VERSION:
        raise ValueError(f"Unsupported tag store version: {data.get('version')}")
    store = TagStore()
    for raw in data.get("entries", []):
        store.set_tags(raw["namespace"], raw["path"], raw.get("tags", []))
    return store
