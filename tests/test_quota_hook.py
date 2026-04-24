"""Tests for vaultpatch.quota_hook."""
import sys
import pytest
from click.testing import CliRunner

from vaultpatch.diff import SecretDiff
from vaultpatch.quota import QuotaConfig, QuotaResult, QuotaViolation
from vaultpatch.quota_hook import abort_on_quota_exceeded, echo_quota_results, run_quota_check


def _diffs(n: int, path: str = "secret/app") -> list[SecretDiff]:
    return [SecretDiff(path=path, key=f"k{i}", old_value="a", new_value="b") for i in range(n)]


def test_run_quota_check_delegates():
    cfg = QuotaConfig(max_changes=100, max_per_path=100)
    result = run_quota_check({"secret/app": _diffs(3)}, cfg)
    assert not result.exceeded


def test_echo_quota_results_no_violations(capsys):
    result = QuotaResult()
    echo_quota_results(result)
    captured = capsys.readouterr()
    assert "passed" in captured.out


def test_echo_quota_results_with_violations(capsys):
    result = QuotaResult()
    result.add(QuotaViolation(path="secret/x", reason="too many", count=9, limit=5))
    echo_quota_results(result)
    captured = capsys.readouterr()
    assert "quota violation" in captured.err
    assert "secret/x" in captured.err


def test_abort_on_quota_exceeded_raises_system_exit():
    result = QuotaResult()
    result.add(QuotaViolation(path="p", reason="r", count=6, limit=3))
    with pytest.raises(SystemExit) as exc_info:
        abort_on_quota_exceeded(result)
    assert exc_info.value.code == 1


def test_abort_on_quota_not_exceeded_does_not_raise():
    result = QuotaResult()
    abort_on_quota_exceeded(result)  # should not raise
