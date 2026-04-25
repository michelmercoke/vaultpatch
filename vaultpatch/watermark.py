"""Watermark support — stamp secrets with metadata on write."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Optional


_DEFAULT_KEY = "_vaultpatch_watermark"


@dataclass
class WatermarkConfig:
    enabled: bool = True
    key: str = _DEFAULT_KEY
    include_user: bool = True
    include_timestamp: bool = True
    extra: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> "WatermarkConfig":
        return cls(
            enabled=data.get("enabled", True),
            key=data.get("key", _DEFAULT_KEY),
            include_user=data.get("include_user", True),
            include_timestamp=data.get("include_timestamp", True),
            extra=data.get("extra", {}),
        )


def _current_user() -> str:
    return os.environ.get("VAULTPATCH_USER") or os.environ.get("USER") or "unknown"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def build_watermark(cfg: WatermarkConfig) -> Optional[str]:
    """Return a compact watermark string, or None when disabled."""
    if not cfg.enabled:
        return None
    parts: Dict[str, str] = {}
    if cfg.include_user:
        parts["user"] = _current_user()
    if cfg.include_timestamp:
        parts["ts"] = _now_iso()
    parts.update(cfg.extra)
    return "|".join(f"{k}={v}" for k, v in parts.items())


def stamp_secret(
    data: Dict[str, str],
    cfg: WatermarkConfig,
    *,
    watermark: Optional[str] = None,
) -> Dict[str, str]:
    """Return a copy of *data* with the watermark key injected.

    If *watermark* is provided it is used directly (useful for testing);
    otherwise :func:`build_watermark` is called.
    """
    if not cfg.enabled:
        return dict(data)
    wm = watermark if watermark is not None else build_watermark(cfg)
    if wm is None:
        return dict(data)
    return {**data, cfg.key: wm}


def strip_watermark(data: Dict[str, str], cfg: WatermarkConfig) -> Dict[str, str]:
    """Return a copy of *data* with the watermark key removed."""
    return {k: v for k, v in data.items() if k != cfg.key}
