"""Tests for vaultpatch.expiry."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from vaultpatch.expiry import (
    ExpiryResult,
    ExpiryViolation,
    ExpiryWarning,
    check_expiry,
    summarise_expiry,
)

_FMT = "%Y-%m-%d"


def _date(offset_days: int) -> str:
    return (datetime.now(tz=timezone.utc) + timedelta(days=offset_days)).strftime(_FMT)


def test_expired_secret_produces_violation():
    secrets = {"__expires_at": _date(-5)}
    result = check_expiry("ns/path", secrets)
    assert result.has_violations
    assert len(result.violations) == 1
    assert result.violations[0].days_overdue == 5


def test_imminent_expiry_produces_warning():
    secrets = {"__expires_at": _date(7)}
    result = check_expiry("ns/path", secrets, warn_days=14)
    assert result.has_warnings
    assert not result.has_violations
    assert result.warnings[0].days_remaining == 7


def test_far_future_expiry_produces_no_warning():
    secrets = {"__expires_at": _date(60)}
    result = check_expiry("ns/path", secrets, warn_days=14)
    assert not result.has_warnings
    assert not result.has_violations


def test_non_expiry_keys_are_ignored():
    secrets = {"username": "admin", "password": "s3cr3t"}
    result = check_expiry("ns/path", secrets)
    assert not result.has_violations
    assert not result.has_warnings


def test_invalid_date_format_is_skipped():
    secrets = {"__expires_at": "not-a-date"}
    result = check_expiry("ns/path", secrets)
    assert not result.has_violations
    assert not result.has_warnings


def test_violation_str_contains_path_and_key():
    v = ExpiryViolation(path="ns/db", key="__expires_at", expires_at="2020-01-01", days_overdue=100)
    assert "ns/db" in str(v)
    assert "100" in str(v)


def test_warning_str_contains_days_remaining():
    w = ExpiryWarning(path="ns/db", key="__expires_at", expires_at="2099-01-01", days_remaining=3)
    assert "3d" in str(w)


def test_summarise_counts_correctly():
    r1 = ExpiryResult(
        violations=[ExpiryViolation("p", "k", "2020-01-01", 1)],
        warnings=[ExpiryWarning("p", "k", "2025-01-01", 5)],
    )
    r2 = ExpiryResult(warnings=[ExpiryWarning("p", "k", "2025-02-01", 10)])
    summary = summarise_expiry([r1, r2])
    assert "1 violation" in summary
    assert "2 warning" in summary
