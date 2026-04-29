"""Persistence layer for fingerprint entries (JSON file-backed store)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import List

from vaultpatch.fingerprint import FingerprintEntry

_VERSION = 1


def save_fingerprints(path: Path, entries: List[FingerprintEntry]) -> None:
    payload = {
        "version": _VERSION,
        "entries": [e.to_dict() for e in entries],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2))


def load_fingerprints(path: Path) -> List[FingerprintEntry]:
    if not path.exists():
        raise FileNotFoundError(f"Fingerprint store not found: {path}")
    payload = json.loads(path.read_text())
    if payload.get("version") != _VERSION:
        raise ValueError(
            f"Unsupported fingerprint store version: {payload.get('version')}"
        )
    return [
        FingerprintEntry(
            path=e["path"],
            namespace=e["namespace"],
            digest=e["digest"],
            keys=e.get("keys", []),
        )
        for e in payload.get("entries", [])
    ]


def fingerprint_store_key(namespace: str) -> str:
    """Return a canonical filename stem for a namespace fingerprint store."""
    safe = namespace.replace("/", "_").replace(" ", "_")
    return f"fingerprints_{safe}.json"
