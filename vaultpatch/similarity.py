"""Detect suspiciously similar secrets across namespaces."""
from __future__ import annotations

import difflib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class SimilarityViolation:
    path_a: str
    key_a: str
    path_b: str
    key_b: str
    ratio: float

    def __str__(self) -> str:
        return (
            f"{self.path_a}::{self.key_a} ~ {self.path_b}::{self.key_b} "
            f"(ratio={self.ratio:.2f})"
        )


@dataclass
class SimilarityResult:
    violations: List[SimilarityViolation] = field(default_factory=list)
    checked: int = 0

    @property
    def has_violations(self) -> bool:
        return bool(self.violations)


@dataclass
class SimilarityConfig:
    threshold: float = 0.85
    ignore_keys: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "SimilarityConfig":
        return cls(
            threshold=float(data.get("threshold", 0.85)),
            ignore_keys=list(data.get("ignore_keys", [])),
        )


def _ratio(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a, b).ratio()


def check_similarity(
    secrets: Dict[str, Dict[str, str]],
    cfg: Optional[SimilarityConfig] = None,
) -> SimilarityResult:
    """Compare secret values across paths and flag near-duplicates.

    Args:
        secrets: mapping of path -> {key: value}
        cfg: similarity configuration
    """
    cfg = cfg or SimilarityConfig()
    result = SimilarityResult()

    items: List[Tuple[str, str, str]] = []
    for path, kvs in secrets.items():
        for key, value in kvs.items():
            if key not in cfg.ignore_keys and value:
                items.append((path, key, value))

    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            path_a, key_a, val_a = items[i]
            path_b, key_b, val_b = items[j]
            result.checked += 1
            ratio = _ratio(val_a, val_b)
            if ratio >= cfg.threshold:
                result.violations.append(
                    SimilarityViolation(
                        path_a=path_a,
                        key_a=key_a,
                        path_b=path_b,
                        key_b=key_b,
                        ratio=ratio,
                    )
                )

    return result
