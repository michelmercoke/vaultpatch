"""Schedule support: parse cron-like run windows and decide if a patch run is permitted."""
from __future__ import annotations

import dataclasses
from datetime import datetime, timezone
from typing import Optional, Sequence


@dataclasses.dataclass(frozen=True)
class ScheduleWindow:
    """A named time window during which patch operations are allowed."""

    name: str
    days: Sequence[int]   # 0=Monday … 6=Sunday (ISO weekday - 1)
    hour_start: int       # inclusive, 0-23
    hour_end: int         # exclusive, 0-23
    timezone_name: str = "UTC"

    def allows(self, at: Optional[datetime] = None) -> bool:
        """Return True when *at* (default: now UTC) falls inside this window."""
        if at is None:
            at = datetime.now(timezone.utc)
        weekday = at.weekday()          # 0=Monday
        hour = at.hour
        return weekday in self.days and self.hour_start <= hour < self.hour_end


@dataclasses.dataclass(frozen=True)
class ScheduleResult:
    allowed: bool
    window: Optional[ScheduleWindow]
    reason: str

    @property
    def blocked(self) -> bool:
        return not self.allowed


def check_schedule(
    windows: Sequence[ScheduleWindow],
    at: Optional[datetime] = None,
) -> ScheduleResult:
    """Return a ScheduleResult indicating whether any window permits a run."""
    if not windows:
        return ScheduleResult(allowed=True, window=None, reason="no schedule configured – always allowed")

    if at is None:
        at = datetime.now(timezone.utc)

    for window in windows:
        if window.allows(at):
            return ScheduleResult(
                allowed=True,
                window=window,
                reason=f"inside window '{window.name}'",
            )

    names = ", ".join(w.name for w in windows)
    return ScheduleResult(
        allowed=False,
        window=None,
        reason=f"outside all configured windows ({names})",
    )


def windows_from_config(raw: list[dict]) -> list[ScheduleWindow]:
    """Build ScheduleWindow objects from the list parsed out of vaultpatch.yaml."""
    result: list[ScheduleWindow] = []
    for entry in raw:
        result.append(
            ScheduleWindow(
                name=entry["name"],
                days=entry["days"],
                hour_start=entry["hour_start"],
                hour_end=entry["hour_end"],
                timezone_name=entry.get("timezone", "UTC"),
            )
        )
    return result
