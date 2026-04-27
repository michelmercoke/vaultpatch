"""Replay audit log entries to reconstruct what was applied at a given time."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator


@dataclass
class ReplayEntry:
    timestamp: str
    namespace: str
    path: str
    mode: str
    changes: list[dict]
    operator: str = ""

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "namespace": self.namespace,
            "path": self.path,
            "mode": self.mode,
            "changes": self.changes,
            "operator": self.operator,
        }


@dataclass
class ReplayResult:
    entries: list[ReplayEntry] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return len(self.errors) == 0

    @property
    def total(self) -> int:
        return len(self.entries)


def _iter_log_lines(log_path: Path) -> Iterator[dict]:
    with log_path.open() as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


def replay_audit_log(
    log_path: Path,
    *,
    namespace: str | None = None,
    since: str | None = None,
    until: str | None = None,
    path_prefix: str | None = None,
) -> ReplayResult:
    """Load and filter audit log entries for replay inspection."""
    result = ReplayResult()

    if not log_path.exists():
        result.errors.append(f"Audit log not found: {log_path}")
        return result

    try:
        for raw in _iter_log_lines(log_path):
            ts = raw.get("timestamp", "")
            ns = raw.get("namespace", "")
            p = raw.get("path", "")

            if namespace and ns != namespace:
                continue
            if since and ts < since:
                continue
            if until and ts > until:
                continue
            if path_prefix and not p.startswith(path_prefix):
                continue

            entry = ReplayEntry(
                timestamp=ts,
                namespace=ns,
                path=p,
                mode=raw.get("mode", "unknown"),
                changes=raw.get("changes", []),
                operator=raw.get("operator", ""),
            )
            result.entries.append(entry)
    except (json.JSONDecodeError, OSError) as exc:
        result.errors.append(str(exc))

    return result


def summarise_replay(result: ReplayResult) -> str:
    if not result.success:
        return f"Replay failed: {'; '.join(result.errors)}"
    return f"{result.total} audit entries matched."
