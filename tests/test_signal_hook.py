"""Tests for vaultpatch.signal_hook."""
from __future__ import annotations

import pytest
from click.testing import CliRunner

from vaultpatch.diff import SecretDiff
from vaultpatch.signal import SignalConfig, SignalResult, SignalViolation
from vaultpatch.signal_hook import (
    abort_on_signal_failure,
    echo_signal_results,
    run_signal_check,
)


def _violation(path: str = "ns/p", key: str = "k") -> SignalViolation:
    return SignalViolation(path=path, key=key, pattern=r"^changeme$", value_snippet="changeme")


def _diff(key: str, new_value: str) -> SecretDiff:
    return SecretDiff(key=key, old_value="old", new_value=new_value)


# ---------------------------------------------------------------------------
# run_signal_check
# ---------------------------------------------------------------------------

def test_run_signal_check_delegates():
    diffs = {"ns/path": [_diff("api_key", "changeme")]}
    results = run_signal_check(diffs)
    assert "ns/path" in results
    assert results["ns/path"].has_violations


def test_run_signal_check_clean_path():
    diffs = {"ns/path": [_diff("api_key", "xK9#mP2$qL7vR")]}
    results = run_signal_check(diffs)
    assert not results["ns/path"].has_violations


def test_run_signal_check_empty_input():
    results = run_signal_check({})
    assert results == {}


# ---------------------------------------------------------------------------
# echo_signal_results
# ---------------------------------------------------------------------------

def test_echo_signal_results_no_violations(capsys):
    results = {"ns/path": SignalResult()}
    echo_signal_results(results)
    out, _ = capsys.readouterr()
    assert "No known-bad" in out


def test_echo_signal_results_with_violations(capsys):
    result = SignalResult(violations=[_violation()])
    echo_signal_results({"ns/path": result})
    _, err = capsys.readouterr()
    assert "SIGNAL" in err
    assert "1 signal violation" in err


# ---------------------------------------------------------------------------
# abort_on_signal_failure
# ---------------------------------------------------------------------------

def test_abort_on_signal_failure_no_violations_does_not_raise():
    results = {"ns/path": SignalResult()}
    abort_on_signal_failure(results)  # should not raise


def test_abort_on_signal_failure_raises_system_exit():
    result = SignalResult(violations=[_violation()])
    with pytest.raises(SystemExit, match="Aborting"):
        abort_on_signal_failure({"ns/path": result})


def test_abort_on_signal_failure_counts_all_paths():
    r1 = SignalResult(violations=[_violation(path="p1")])
    r2 = SignalResult(violations=[_violation(path="p2"), _violation(path="p2", key="k2")])
    with pytest.raises(SystemExit, match="3"):
        abort_on_signal_failure({"p1": r1, "p2": r2})
