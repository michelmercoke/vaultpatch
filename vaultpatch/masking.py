"""masking.py — enforce output masking rules on secret values before display."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

_DEFAULT_MASK = "***"
_DEFAULT_VISIBLE_CHARS = 4


@dataclass
class MaskingConfig:
    """Controls how secret values are masked in output."""
    enabled: bool = True
    mask_string: str = _DEFAULT_MASK
    # Number of trailing chars to reveal (0 = fully masked)
    visible_suffix_chars: int = _DEFAULT_VISIBLE_CHARS
    # Keys whose values should always be fully masked regardless of suffix setting
    always_full_mask_keys: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "MaskingConfig":
        return cls(
            enabled=data.get("enabled", True),
            mask_string=data.get("mask_string", _DEFAULT_MASK),
            visible_suffix_chars=int(data.get("visible_suffix_chars", _DEFAULT_VISIBLE_CHARS)),
            always_full_mask_keys=list(data.get("always_full_mask_keys", [])),
        )


@dataclass
class MaskResult:
    key: str
    original: Optional[str]
    masked: Optional[str]
    fully_masked: bool


def mask_value(
    key: str,
    value: Optional[str],
    config: MaskingConfig,
) -> MaskResult:
    """Return a MaskResult for a single key/value pair."""
    if not config.enabled or value is None:
        return MaskResult(key=key, original=value, masked=value, fully_masked=False)

    force_full = key in config.always_full_mask_keys
    n = config.visible_suffix_chars

    if force_full or n == 0 or len(value) <= n:
        masked = config.mask_string
        fully_masked = True
    else:
        masked = config.mask_string + value[-n:]
        fully_masked = False

    return MaskResult(key=key, original=value, masked=masked, fully_masked=fully_masked)


def mask_secrets(
    secrets: dict,
    config: MaskingConfig,
) -> dict:
    """Return a new dict with all values replaced by their masked forms."""
    return {
        k: mask_value(k, v, config).masked
        for k, v in secrets.items()
    }
