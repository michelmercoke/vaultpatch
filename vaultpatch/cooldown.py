"""Cooldown enforcement: prevent re-applying changes to the same path within a time window."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional

_DEFAULT_COOLDOWN_SECONDS = 300  # 5 minutes
_STORE_VERSION = 1


@dataclass
class CooldownEntry:
    path: str
    namespace: str
    applied_at: str  # ISO-8601
    cooldown_seconds: int

    def is_active(self, now: Optional[datetime] = None) -> bool:
        now = now or datetime.now(timezone.utc)
        applied = datetime.fromisoformat(self.applied_at)
        expires = applied + timedelta(seconds=self.cooldown_seconds)
        return now < expires

    def expires_at(self) -> datetime:
        applied = datetime.fromisoformat(self.applied_at)
        return applied + timedelta(seconds=self.cooldown_seconds)

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "namespace": self.namespace,
            "applied_at": self.applied_at,
            "cooldown_seconds": self.cooldown_seconds,
        }


@dataclass
class CooldownStore:
    _entries: Dict[str, CooldownEntry] = field(default_factory=dict)

    def _key(self, namespace: str, path: str) -> str:
        return f"{namespace}::{path}"

    def record(self, namespace: str, path: str, cooldown_seconds: int = _DEFAULT_COOLDOWN_SECONDS) -> CooldownEntry:
        entry = CooldownEntry(
            path=path,
            namespace=namespace,
            applied_at=datetime.now(timezone.utc).isoformat(),
            cooldown_seconds=cooldown_seconds,
        )
        self._entries[self._key(namespace, path)] = entry
        return entry

    def get(self, namespace: str, path: str) -> Optional[CooldownEntry]:
        return self._entries.get(self._key(namespace, path))

    def is_blocked(self, namespace: str, path: str, now: Optional[datetime] = None) -> bool:
        entry = self.get(namespace, path)
        return entry is not None and entry.is_active(now)

    def all_entries(self) -> List[CooldownEntry]:
        return list(self._entries.values())

    def save(self, filepath: Path) -> None:
        data = {
            "version": _STORE_VERSION,
            "entries": [e.to_dict() for e in self._entries.values()],
        }
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(json.dumps(data, indent=2))

    @classmethod
    def load(cls, filepath: Path) -> "CooldownStore":
        if not filepath.exists():
            return cls()
        data = json.loads(filepath.read_text())
        if data.get("version") != _STORE_VERSION:
            raise ValueError(f"Unsupported cooldown store version: {data.get('version')}")
        store = cls()
        for raw in data.get("entries", []):
            entry = CooldownEntry(**raw)
            store._entries[store._key(entry.namespace, entry.path)] = entry
        return store
