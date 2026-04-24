"""Secret write quota enforcement — limits how many secrets can be patched per run."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from vaultpatch.diff import SecretDiff


@dataclass
class QuotaConfig:
    max_changes: int = 50
    max_per_path: int = 20

    @classmethod
    def from_dict(cls, data: dict) -> "QuotaConfig":
        return cls(
            max_changes=int(data.get("max_changes", 50)),
            max_per_path=int(data.get("max_per_path", 20)),
        )


@dataclass
class QuotaViolation:
    path: str
    reason: str
    count: int
    limit: int

    def __str__(self) -> str:
        return f"{self.path}: {self.reason} ({self.count} > {self.limit})"


@dataclass
class QuotaResult:
    violations: List[QuotaViolation] = field(default_factory=list)

    @property
    def exceeded(self) -> bool:
        return len(self.violations) > 0

    def add(self, v: QuotaViolation) -> None:
        self.violations.append(v)


def check_quota(
    diffs_by_path: dict[str, List[SecretDiff]],
    config: QuotaConfig,
) -> QuotaResult:
    """Check that the total and per-path change counts are within quota."""
    result = QuotaResult()

    total = sum(len(d) for d in diffs_by_path.values())
    if total > config.max_changes:
        result.add(
            QuotaViolation(
                path="(all paths)",
                reason="total changes exceed max_changes",
                count=total,
                limit=config.max_changes,
            )
        )

    for path, diffs in diffs_by_path.items():
        count = len(diffs)
        if count > config.max_per_path:
            result.add(
                QuotaViolation(
                    path=path,
                    reason="per-path changes exceed max_per_path",
                    count=count,
                    limit=config.max_per_path,
                )
            )

    return result
