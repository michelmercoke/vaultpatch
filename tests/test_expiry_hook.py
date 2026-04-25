"""Tests for vaultpatch.expiry_hook."""
from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from vaultpatch.expiry import ExpiryResult, ExpiryViolation, ExpiryWarning
from vaultpatch.expiry_hook import abort_on_expiry, echo_expiry_results, run_expiry_check

_FMT = "%Y-%m-%d"


def _date(offset: int) -> str:
    return (datetime.now(tz=timezone.utc) + timedelta(days=offset)).strftime(_FMT)


def test_run_expiry_check_returns_results_per_path():
    path_secrets = {
        "ns/db": {"__expires_at": _date(-1)},
        "ns/app": {"api_key": "abc123"},
    }
    results = run_expiry_check(path_secrets, warn_days=14)
    assert len(results) == 2


def test_run_expiry_check_detects_violation():
    path_secrets = {"ns/db": {"__expires_at": _date(-10)}}
    results = run_expiry_check(path_secrets)
    assert results[0].has_violations


def test_echo_expiry_results_prints_warning(capsys):
    results = [
        ExpiryResult(warnings=[ExpiryWarning("ns/db", "__expires_at", "2099-01-01", 5)])
    ]
    echo_expiry_results(results)
    captured = capsys.readouterr()
    assert "WARN" in captured.out


def test_echo_expiry_results_prints_violation(capsys):
    results = [
        ExpiryResult(violations=[ExpiryViolation("ns/db", "__expires_at", "2020-01-01", 30)])
    ]
    echo_expiry_results(results)
    captured = capsys.readouterr()
    assert "EXPIRED" in captured.err


def test_abort_on_expiry_raises_system_exit():
    results = [
        ExpiryResult(violations=[ExpiryViolation("ns/db", "__expires_at", "2020-01-01", 1)])
    ]
    with pytest.raises(SystemExit) as exc_info:
        abort_on_expiry(results)
    assert exc_info.value.code == 1


def test_abort_on_expiry_no_exit_when_clean():
    results = [ExpiryResult()]
    # Should not raise
    abort_on_expiry(results)
