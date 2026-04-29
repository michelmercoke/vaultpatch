"""Fingerprint module: compute and compare content hashes for secret paths."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class FingerprintEntry:
    path: str
    namespace: str
    digest: str
    keys: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "namespace": self.namespace,
            "digest": self.digest,
            "keys": sorted(self.keys),
        }


@dataclass
class FingerprintMismatch:
    path: str
    namespace: str
    stored: str
    current: str

    def __str__(self) -> str:
        return (
            f"{self.namespace}/{self.path}: digest mismatch "
            f"(stored={self.stored[:8]}, current={self.current[:8]})"
        )


@dataclass
class FingerprintResult:
    entries: List[FingerprintEntry] = field(default_factory=list)
    mismatches: List[FingerprintMismatch] = field(default_factory=list)

    @property
    def has_mismatches(self) -> bool:
        return bool(self.mismatches)


def _compute_digest(secrets: Dict[str, str]) -> str:
    """Stable SHA-256 digest of a sorted key-value mapping."""
    canonical = json.dumps(secrets, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


def build_fingerprint(path: str, namespace: str, secrets: Dict[str, str]) -> FingerprintEntry:
    return FingerprintEntry(
        path=path,
        namespace=namespace,
        digest=_compute_digest(secrets),
        keys=list(secrets.keys()),
    )


def compare_fingerprints(
    stored: List[FingerprintEntry],
    current: List[FingerprintEntry],
) -> FingerprintResult:
    stored_map = {(e.namespace, e.path): e for e in stored}
    result = FingerprintResult(entries=current)
    for entry in current:
        key = (entry.namespace, entry.path)
        prev = stored_map.get(key)
        if prev and prev.digest != entry.digest:
            result.mismatches.append(
                FingerprintMismatch(
                    path=entry.path,
                    namespace=entry.namespace,
                    stored=prev.digest,
                    current=entry.digest,
                )
            )
    return result
