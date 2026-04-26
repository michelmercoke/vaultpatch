"""Rate limiting for Vault write operations across namespaces."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional
import json


@dataclass
class RateLimitConfig:
    max_writes_per_minute: int = 60
    max_writes_per_hour: int = 500
    namespace: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "RateLimitConfig":
        return cls(
            max_writes_per_minute=data.get("max_writes_per_minute", 60),
            max_writes_per_hour=data.get("max_writes_per_hour", 500),
            namespace=data.get("namespace"),
        )


@dataclass
class RateLimitViolation:
    namespace: str
    window: str
    limit: int
    actual: int

    def __str__(self) -> str:
        return (
            f"Rate limit exceeded for '{self.namespace}': "
            f"{self.actual} writes in {self.window} (limit {self.limit})"
        )


@dataclass
class RateLimitResult:
    namespace: str
    violations: List[RateLimitViolation] = field(default_factory=list)

    @property
    def has_violations(self) -> bool:
        return len(self.violations) > 0


@dataclass
class RateLimitStore:
    _path: Path
    _data: Dict[str, List[float]] = field(default_factory=dict)

    @classmethod
    def load(cls, path: Path) -> "RateLimitStore":
        store = cls(_path=path)
        if path.exists():
            raw = json.loads(path.read_text())
            store._data = {k: list(v) for k, v in raw.items()}
        return store

    def save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(self._data))

    def record(self, namespace: str) -> None:
        now = time.time()
        self._data.setdefault(namespace, []).append(now)

    def writes_in_window(self, namespace: str, seconds: int) -> int:
        now = time.time()
        cutoff = now - seconds
        return sum(1 for t in self._data.get(namespace, []) if t >= cutoff)

    def prune(self, namespace: str, max_age: int = 3600) -> None:
        cutoff = time.time() - max_age
        self._data[namespace] = [
            t for t in self._data.get(namespace, []) if t >= cutoff
        ]


def check_rate_limit(namespace: str, cfg: RateLimitConfig, store: RateLimitStore) -> RateLimitResult:
    result = RateLimitResult(namespace=namespace)
    per_minute = store.writes_in_window(namespace, 60)
    if per_minute >= cfg.max_writes_per_minute:
        result.violations.append(RateLimitViolation(
            namespace=namespace,
            window="1 minute",
            limit=cfg.max_writes_per_minute,
            actual=per_minute,
        ))
    per_hour = store.writes_in_window(namespace, 3600)
    if per_hour >= cfg.max_writes_per_hour:
        result.violations.append(RateLimitViolation(
            namespace=namespace,
            window="1 hour",
            limit=cfg.max_writes_per_hour,
            actual=per_hour,
        ))
    return result
