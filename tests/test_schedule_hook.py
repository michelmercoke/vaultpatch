"""Tests for vaultpatch.schedule_hook."""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from vaultpatch.schedule import ScheduleWindow, ScheduleResult
from vaultpatch.schedule_hook import enforce_schedule, echo_schedule_status

# Monday 10:00 UTC – inside business hours
INSIDE = datetime(2024, 1, 8, 10, 0, tzinfo=timezone.utc)
# Saturday 03:00 UTC – outside
OUTSIDE = datetime(2024, 1, 13, 3, 0, tzinfo=timezone.utc)

WINDOW = ScheduleWindow(name="biz", days=[0, 1, 2, 3, 4], hour_start=9, hour_end=17)


def test_enforce_schedule_allowed_does_not_raise():
    result = enforce_schedule([WINDOW], at=INSIDE)
    assert result.allowed is True


def test_enforce_schedule_blocked_raises_system_exit():
    with pytest.raises(SystemExit):
        enforce_schedule([WINDOW], at=OUTSIDE)


def test_enforce_schedule_dry_run_does_not_raise():
    # Should NOT raise even when blocked
    result = enforce_schedule([WINDOW], at=OUTSIDE, dry_run=True)
    assert result.blocked is True


def test_enforce_schedule_prints_allowed(capsys):
    enforce_schedule([WINDOW], at=INSIDE)
    out = capsys.readouterr().out
    assert "✓" in out


def test_enforce_schedule_prints_blocked_to_stderr(capsys):
    with pytest.raises(SystemExit):
        enforce_schedule([WINDOW], at=OUTSIDE)
    err = capsys.readouterr().err
    assert "✗" in err


def test_echo_schedule_status_allowed(capsys):
    result = ScheduleResult(allowed=True, window=WINDOW, reason="inside window 'biz'")
    echo_schedule_status(result)
    out = capsys.readouterr().out
    assert "✓" in out
    assert "biz" in out


def test_echo_schedule_status_blocked(capsys):
    result = ScheduleResult(allowed=False, window=None, reason="outside all windows")
    echo_schedule_status(result)
    out = capsys.readouterr().out
    assert "✗" in out
