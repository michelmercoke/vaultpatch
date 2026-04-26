"""Tests for vaultpatch.ratelimit_hook."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import List
from unittest.mock import MagicMock, patch

import pytest

from vaultpatch.ratelimit import RateLimitConfig, RateLimitResult, RateLimitStore, RateLimitViolation
from vaultpatch.ratelimit_hook import (
    abort_on_rate_limit_exceeded,
    echo_rate_limit_results,
    record_writes,
    run_rate_limit_check,
)


@pytest.fixture
def tmp_store(tmp_path: Path) -> RateLimitStore:
    return RateLimitStore.load(tmp_path / "ratelimit.json")


def _violation() -> RateLimitViolation:
    return RateLimitViolation(namespace="ns/prod", window="1 minute", limit=5, actual=7)


def test_run_rate_limit_check_no_violation(tmp_store: RateLimitStore) -> None:
    cfg = RateLimitConfig(max_writes_per_minute=100, max_writes_per_hour=1000)
    result = run_rate_limit_check("ns/dev", cfg, tmp_store)
    assert not result.has_violations


def test_run_rate_limit_check_detects_violation(tmp_store: RateLimitStore) -> None:
    cfg = RateLimitConfig(max_writes_per_minute=2, max_writes_per_hour=1000)
    for _ in range(2):
        tmp_store.record("ns/dev")
    result = run_rate_limit_check("ns/dev", cfg, tmp_store)
    assert result.has_violations


def test_echo_rate_limit_results_ok(capsys) -> None:
    results = [RateLimitResult(namespace="ns/dev")]
    echo_rate_limit_results(results)
    out = capsys.readouterr().out
    assert "OK" in out
    assert "ns/dev" in out


def test_echo_rate_limit_results_violation(capsys) -> None:
    result = RateLimitResult(namespace="ns/prod", violations=[_violation()])
    echo_rate_limit_results([result])
    captured = capsys.readouterr()
    assert "rate-limit" in captured.err
    assert "ns/prod" in captured.err


def test_abort_on_rate_limit_exceeded_raises(tmp_store: RateLimitStore) -> None:
    result = RateLimitResult(namespace="ns/prod", violations=[_violation()])
    with pytest.raises(SystemExit):
        abort_on_rate_limit_exceeded([result])


def test_abort_on_rate_limit_no_violation_does_not_raise() -> None:
    results = [RateLimitResult(namespace="ns/dev")]
    abort_on_rate_limit_exceeded(results)  # should not raise


def test_record_writes_increments_store(tmp_store: RateLimitStore) -> None:
    record_writes("ns/dev", 4, tmp_store)
    assert tmp_store.writes_in_window("ns/dev", 60) == 4
