"""Immutable key enforcement — prevent changes to keys marked as immutable."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from vaultpatch.diff import SecretDiff


@dataclass
class ImmutableViolation:
    path: str
    key: str
    reason: str = "key is marked immutable"

    def __str__(self) -> str:
        return f"{self.path}::{self.key} — {self.reason}"


@dataclass
class ImmutableResult:
    violations: list[ImmutableViolation] = field(default_factory=list)

    @property
    def has_violations(self) -> bool:
        return bool(self.violations)


@dataclass
class ImmutableConfig:
    """Holds a set of key patterns that must never be modified once written."""
    keys: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "ImmutableConfig":
        return cls(keys=list(data.get("immutable_keys", [])))

    def is_immutable(self, key: str) -> bool:
        import fnmatch
        return any(fnmatch.fnmatch(key, pattern) for pattern in self.keys)


def check_immutable(
    diffs: Iterable[SecretDiff],
    config: ImmutableConfig,
) -> ImmutableResult:
    """Return violations for any diff that modifies or removes an immutable key."""
    result = ImmutableResult()
    for diff in diffs:
        if diff.is_added:
            # Adding a key for the first time is allowed
            continue
        if config.is_immutable(diff.key):
            result.violations.append(
                ImmutableViolation(path=diff.path, key=diff.key)
            )
    return result


def summarise_immutable(result: ImmutableResult) -> str:
    if not result.has_violations:
        return "immutable check passed — no violations"
    lines = [f"immutable violations ({len(result.violations)}):"] + [
        f"  - {v}" for v in result.violations
    ]
    return "\n".join(lines)
