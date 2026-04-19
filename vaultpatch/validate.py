"""Validate secret values against simple rules before applying patches."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from vaultpatch.diff import SecretDiff


@dataclass
class ValidationError:
    path: str
    key: str
    message: str

    def __str__(self) -> str:
        return f"{self.path}:{self.key} — {self.message}"


@dataclass
class ValidationResult:
    errors: List[ValidationError] = field(default_factory=list)

    @property
    def valid(self) -> bool:
        return len(self.errors) == 0

    def add(self, path: str, key: str, message: str) -> None:
        self.errors.append(ValidationError(path=path, key=key, message=message))


def _check_value(value: str) -> Optional[str]:
    """Return an error message if the value fails basic checks, else None."""
    if not isinstance(value, str):
        return "value must be a string"
    if len(value.strip()) == 0:
        return "value must not be blank"
    if len(value) > 4096:
        return "value exceeds maximum length of 4096 characters"
    return None


def validate_diffs(diffs: List[SecretDiff]) -> ValidationResult:
    """Validate all incoming (added/changed) secret values in a diff list."""
    result = ValidationResult()
    for diff in diffs:
        if diff.is_removed:
            continue
        new_val = diff.new_value
        if new_val is None:
            result.add(diff.path, diff.key, "new value is missing")
            continue
        msg = _check_value(new_val)
        if msg:
            result.add(diff.path, diff.key, msg)
    return result


def validate_keys(diffs: List[SecretDiff], forbidden: List[str]) -> ValidationResult:
    """Reject diffs whose keys appear in the forbidden list."""
    result = ValidationResult()
    forbidden_set = {k.lower() for k in forbidden}
    for diff in diffs:
        if diff.key.lower() in forbidden_set:
            result.add(diff.path, diff.key, f"key '{diff.key}' is forbidden")
    return result
