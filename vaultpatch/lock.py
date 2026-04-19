"""Advisory lock mechanism to prevent concurrent vaultpatch runs on the same namespace."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_LOCK_DIR = Path("/tmp/vaultpatch/locks")
DEFAULT_TTL = 300  # seconds


@dataclass
class LockResult:
    namespace: str
    acquired: bool
    lock_file: Path
    error: str = ""

    @property
    def success(self) -> bool:
        return self.acquired


def _lock_path(namespace: str, lock_dir: Path) -> Path:
    safe = namespace.replace("/", "_").replace(" ", "_")
    return lock_dir / f"{safe}.lock"


def acquire_lock(
    namespace: str,
    lock_dir: Path = DEFAULT_LOCK_DIR,
    ttl: int = DEFAULT_TTL,
) -> LockResult:
    lock_dir.mkdir(parents=True, exist_ok=True)
    path = _lock_path(namespace, lock_dir)

    if path.exists():
        try:
            age = time.time() - path.stat().st_mtime
            if age < ttl:
                return LockResult(
                    namespace=namespace,
                    acquired=False,
                    lock_file=path,
                    error=f"Lock held for {int(age)}s (TTL={ttl}s)",
                )
            path.unlink()  # stale lock
        except OSError as exc:
            return LockResult(namespace=namespace, acquired=False, lock_file=path, error=str(exc))

    try:
        path.write_text(str(os.getpid()))
        return LockResult(namespace=namespace, acquired=True, lock_file=path)
    except OSError as exc:
        return LockResult(namespace=namespace, acquired=False, lock_file=path, error=str(exc))


def release_lock(namespace: str, lock_dir: Path = DEFAULT_LOCK_DIR) -> bool:
    path = _lock_path(namespace, lock_dir)
    try:
        path.unlink(missing_ok=True)
        return True
    except OSError:
        return False
