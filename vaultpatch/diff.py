"""Diff secrets between two Vault namespaces or a local patch file."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class SecretDiff:
    path: str
    key: str
    old_value: Any
    new_value: Any

    @property
    def is_added(self) -> bool:
        return self.old_value is None and self.new_value is not None

    @property
    def is_removed(self) -> bool:
        return self.old_value is not None and self.new_value is None

    @property
    def is_changed(self) -> bool:
        return self.old_value is not None and self.new_value is not None and self.old_value != self.new_value

    def label(self) -> str:
        if self.is_added:
            return "added"
        if self.is_removed:
            return "removed"
        if self.is_changed:
            return "changed"
        return "unchanged"


def diff_secrets(
    path: str,
    current: dict[str, Any],
    desired: dict[str, Any],
) -> list[SecretDiff]:
    """Return a list of SecretDiff entries for all keys that differ."""
    diffs: list[SecretDiff] = []
    all_keys = set(current) | set(desired)
    for key in sorted(all_keys):
        old_val = current.get(key)
        new_val = desired.get(key)
        if old_val != new_val:
            diffs.append(SecretDiff(path=path, key=key, old_value=old_val, new_value=new_val))
    return diffs


def format_diff(diffs: list[SecretDiff], redact: bool = True) -> str:
    """Render diffs as a human-readable string."""
    if not diffs:
        return "No differences found."
    lines: list[str] = []
    for d in diffs:
        old = "<redacted>" if redact and d.old_value is not None else repr(d.old_value)
        new = "<redacted>" if redact and d.new_value is not None else repr(d.new_value)
        lines.append(f"[{d.label().upper()}] {d.path}#{d.key}: {old} -> {new}")
    return "\n".join(lines)
