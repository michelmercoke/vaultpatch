"""Tests for vaultpatch.retry."""
import pytest
from unittest.mock import MagicMock
from vaultpatch.retry import RetryConfig, RetryResult, with_retry


def _no_sleep(seconds: float) -> None:  # noqa: ARG001
    pass


def test_success_on_first_attempt():
    fn = MagicMock(return_value="ok")
    result = with_retry(fn, sleep_fn=_no_sleep)
    assert result.success is True
    assert result.value == "ok"
    assert result.attempts_made == 1


def test_retries_on_connection_error():
    calls = []

    def flaky():
        calls.append(1)
        if len(calls) < 3:
            raise ConnectionError("down")
        return "recovered"

    result = with_retry(flaky, RetryConfig(attempts=3, delay=0), sleep_fn=_no_sleep)
    assert result.success is True
    assert result.value == "recovered"
    assert result.attempts_made == 3


def test_exhausts_all_attempts():
    fn = MagicMock(side_effect=ConnectionError("always down"))
    cfg = RetryConfig(attempts=3, delay=0)
    result = with_retry(fn, cfg, sleep_fn=_no_sleep)
    assert result.success is False
    assert result.attempts_made == 3
    assert "always down" in (result.error or "")


def test_non_retryable_exception_stops_immediately():
    fn = MagicMock(side_effect=ValueError("bad input"))
    cfg = RetryConfig(attempts=5, delay=0)
    result = with_retry(fn, cfg, sleep_fn=_no_sleep)
    assert result.success is False
    assert result.attempts_made == 1
    assert "bad input" in (result.error or "")


def test_backoff_delay_increases():
    delays: list[float] = []
    calls = [0]

    def flaky():
        calls[0] += 1
        if calls[0] < 3:
            raise ConnectionError("retry")
        return "done"

    with_retry(
        flaky,
        RetryConfig(attempts=3, delay=1.0, backoff=2.0),
        sleep_fn=delays.append,
    )
    assert delays == [1.0, 2.0]


def test_default_config_used_when_none_provided():
    fn = MagicMock(return_value=42)
    result = with_retry(fn, sleep_fn=_no_sleep)
    assert result.success is True
    assert result.value == 42
