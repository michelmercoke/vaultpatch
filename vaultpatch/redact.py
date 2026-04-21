"""Redaction utilities for masking sensitive secret values in output."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from vaultpatch.diff import SecretDiff

_REDACTED = "***REDACTED***"

# Keys whose values should always be redacted regardless of user config
_DEFAULT_SENSITIVE_PATTERNS = (
    "password",
    "secret",
    "token",
    "api_key",
    "private_key",
    "credential",
)


@dataclass
class RedactConfig:
    """Controls which keys are considered sensitive."""

    extra_patterns: list[str] = field(default_factory=list)
    redact_all: bool = False

    def is_sensitive(self, key: str) -> bool:
        """Return True if *key* should have its value redacted."""
        if self.redact_all:
            return True
        lower = key.lower()
        for pattern in _DEFAULT_SENSITIVE_PATTERNS:
            if pattern in lower:
                return True
        for pattern in self.extra_patterns:
            if pattern.lower() in lower:
                return True
        return False


def redact_value(value: str | None, key: str, cfg: RedactConfig) -> str | None:
    """Return *value* unchanged, or the redaction marker if the key is sensitive."""
    if value is None:
        return None
    return _REDACTED if cfg.is_sensitive(key) else value


def redact_diff(diff: SecretDiff, cfg: RedactConfig) -> SecretDiff:
    """Return a copy of *diff* with sensitive values masked."""
    return SecretDiff(
        path=diff.path,
        key=diff.key,
        old_value=redact_value(diff.old_value, diff.key, cfg),
        new_value=redact_value(diff.new_value, diff.key, cfg),
    )


def redact_diffs(
    diffs: Iterable[SecretDiff], cfg: RedactConfig | None = None
) -> list[SecretDiff]:
    """Return a list of diffs with sensitive values masked.

    Uses a default *RedactConfig* when *cfg* is not supplied.
    """
    effective_cfg = cfg if cfg is not None else RedactConfig()
    return [redact_diff(d, effective_cfg) for d in diffs]
