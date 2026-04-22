"""Pin module: record and enforce expected secret versions per path."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

PIN_FILE_VERSION = 1


@dataclass
class PinEntry:
    path: str
    namespace: str
    version: int
    note: str = ""

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "namespace": self.namespace,
            "version": self.version,
            "note": self.note,
        }


@dataclass
class PinStore:
    _pins: Dict[str, PinEntry] = field(default_factory=dict)

    @staticmethod
    def _key(namespace: str, path: str) -> str:
        return f"{namespace}::{path}"

    def set(self, entry: PinEntry) -> None:
        self._pins[self._key(entry.namespace, entry.path)] = entry

    def get(self, namespace: str, path: str) -> Optional[PinEntry]:
        return self._pins.get(self._key(namespace, path))

    def remove(self, namespace: str, path: str) -> bool:
        key = self._key(namespace, path)
        if key in self._pins:
            del self._pins[key]
            return True
        return False

    def all_entries(self) -> list[PinEntry]:
        return list(self._pins.values())

    def to_dict(self) -> dict:
        return {
            "version": PIN_FILE_VERSION,
            "pins": [e.to_dict() for e in self._pins.values()],
        }


def save_pins(store: PinStore, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(store.to_dict(), indent=2))


def load_pins(path: Path) -> PinStore:
    if not path.exists():
        raise FileNotFoundError(f"Pin file not found: {path}")
    data = json.loads(path.read_text())
    if data.get("version") != PIN_FILE_VERSION:
        raise ValueError(f"Unsupported pin file version: {data.get('version')}")
    store = PinStore()
    for item in data.get("pins", []):
        store.set(PinEntry(**item))
    return store


def check_pin(store: PinStore, namespace: str, path: str, actual_version: int) -> Optional[str]:
    """Return an error message if the actual version violates the pin, else None."""
    entry = store.get(namespace, path)
    if entry is None:
        return None
    if actual_version != entry.version:
        return (
            f"Version mismatch for {namespace}::{path}: "
            f"pinned={entry.version}, actual={actual_version}"
        )
    return None
