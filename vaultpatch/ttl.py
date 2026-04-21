"""TTL (time-to-live) tracking for secrets — detects secrets approaching or past expiry."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


_DEFAULT_WARN_DAYS = 7


@dataclass
class TTLEntry:
    path: str
    namespace: str
    expires_at: datetime
    warn_days: int = _DEFAULT_WARN_DAYS

    @property
    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) >= self.expires_at

    @property
    def days_remaining(self) -> float:
        delta = self.expires_at - datetime.now(timezone.utc)
        return delta.total_seconds() / 86400

    @property
    def is_warning(self) -> bool:
        return not self.is_expired and self.days_remaining <= self.warn_days

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "namespace": self.namespace,
            "expires_at": self.expires_at.isoformat(),
            "days_remaining": round(self.days_remaining, 2),
            "is_expired": self.is_expired,
            "is_warning": self.is_warning,
        }


@dataclass
class TTLReport:
    entries: List[TTLEntry] = field(default_factory=list)

    @property
    def expired(self) -> List[TTLEntry]:
        return [e for e in self.entries if e.is_expired]

    @property
    def warning(self) -> List[TTLEntry]:
        return [e for e in self.entries if e.is_warning]

    @property
    def healthy(self) -> List[TTLEntry]:
        return [e for e in self.entries if not e.is_expired and not e.is_warning]


def check_ttl(metadata: Dict[str, str], namespace: str, warn_days: int = _DEFAULT_WARN_DAYS) -> TTLReport:
    """Build a TTLReport from a mapping of path -> ISO expiry string."""
    report = TTLReport()
    for path, expiry_str in metadata.items():
        try:
            expires_at = datetime.fromisoformat(expiry_str)
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        report.entries.append(
            TTLEntry(path=path, namespace=namespace, expires_at=expires_at, warn_days=warn_days)
        )
    return report
