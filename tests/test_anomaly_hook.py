"""Tests for vaultpatch.anomaly_hook."""
import sys
import pytest
from unittest.mock import patch

from vaultpatch.anomaly import AnomalyConfig, AnomalyResult, AnomalyViolation
from vaultpatch.anomaly_hook import (
    abort_on_anomaly_failure,
    echo_anomaly_results,
    run_anomaly_check,
)
from vaultpatch.diff import SecretDiff


def _diff(key: str, new: str) -> SecretDiff:
    return SecretDiff(key=key, old_value=None, new_value=new)


def _violation(path: str = "ns/p", key: str = "k") -> AnomalyViolation:
    return AnomalyViolation(path=path, key=key, reason="too short (1 < 8)")


def test_run_anomaly_check_delegates():
    diffs = {"ns/path": [_diff("token", "x" * 12)]}
    cfg = AnomalyConfig(min_length=4)
    results = run_anomaly_check(diffs, cfg)
    assert "ns/path" in results
    assert not results["ns/path"].has_violations


def test_run_anomaly_check_detects_violation():
    diffs = {"ns/path": [_diff("token", "abc")]}
    cfg = AnomalyConfig(min_length=8)
    results = run_anomaly_check(diffs, cfg)
    assert results["ns/path"].has_violations


def test_echo_anomaly_results_ok(capsys):
    results = {"ns/path": AnomalyResult(violations=[])}
    echo_anomaly_results(results)
    out = capsys.readouterr().out
    assert "OK" in out


def test_echo_anomaly_results_violation(capsys):
    v = _violation()
    results = {"ns/path": AnomalyResult(violations=[v])}
    echo_anomaly_results(results)
    err = capsys.readouterr().err
    assert "WARN" in err


def test_abort_on_anomaly_failure_no_violations_does_not_raise():
    results = {"ns/path": AnomalyResult(violations=[])}
    abort_on_anomaly_failure(results)  # should not raise


def test_abort_on_anomaly_failure_raises_system_exit():
    v = _violation()
    results = {"ns/path": AnomalyResult(violations=[v])}
    with pytest.raises(SystemExit) as exc_info:
        abort_on_anomaly_failure(results)
    assert exc_info.value.code == 1
