"""Tests for vaultpatch.schedule."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from vaultpatch.schedule import (
    ScheduleWindow,
    ScheduleResult,
    check_schedule,
    windows_from_config,
)

# Monday 10:30 UTC
MON_10_30 = datetime(2024, 1, 8, 10, 30, tzinfo=timezone.utc)   # weekday=0
# Saturday 03:00 UTC
SAT_03_00 = datetime(2024, 1, 13, 3, 0, tzinfo=timezone.utc)    # weekday=5


@pytest.fixture()
def weekday_window() -> ScheduleWindow:
    return ScheduleWindow(name="business-hours", days=[0, 1, 2, 3, 4], hour_start=9, hour_end=17)


def test_window_allows_when_inside(weekday_window):
    assert weekday_window.allows(MON_10_30) is True


def test_window_blocks_weekend(weekday_window):
    assert weekday_window.allows(SAT_03_00) is False


def test_window_blocks_outside_hours(weekday_window):
    after_hours = datetime(2024, 1, 8, 18, 0, tzinfo=timezone.utc)
    assert weekday_window.allows(after_hours) is False


def test_window_hour_end_is_exclusive(weekday_window):
    on_boundary = datetime(2024, 1, 8, 17, 0, tzinfo=timezone.utc)
    assert weekday_window.allows(on_boundary) is False


def test_check_schedule_no_windows_always_allowed():
    result = check_schedule([], at=SAT_03_00)
    assert result.allowed is True
    assert "always allowed" in result.reason


def test_check_schedule_inside_window(weekday_window):
    result = check_schedule([weekday_window], at=MON_10_30)
    assert result.allowed is True
    assert result.window is weekday_window


def test_check_schedule_outside_all_windows(weekday_window):
    result = check_schedule([weekday_window], at=SAT_03_00)
    assert result.allowed is False
    assert result.window is None
    assert "business-hours" in result.reason


def test_schedule_result_blocked_property(weekday_window):
    result = check_schedule([weekday_window], at=SAT_03_00)
    assert result.blocked is True


def test_windows_from_config_builds_objects():
    raw = [
        {"name": "nightly", "days": [0, 1, 2, 3, 4, 5, 6], "hour_start": 2, "hour_end": 4}
    ]
    windows = windows_from_config(raw)
    assert len(windows) == 1
    assert windows[0].name == "nightly"
    assert windows[0].hour_start == 2


def test_windows_from_config_default_timezone():
    raw = [{"name": "w", "days": [0], "hour_start": 0, "hour_end": 1}]
    windows = windows_from_config(raw)
    assert windows[0].timezone_name == "UTC"
