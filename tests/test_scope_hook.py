"""Tests for vaultpatch/scope_hook.py"""
import pytest
from click.testing import CliRunner

from vaultpatch.scope import ScopeConfig, ScopeViolation, ScopeResult
from vaultpatch.scope_hook import (
    abort_on_scope_violation,
    echo_scope_results,
    run_scope_check,
)


# ---------------------------------------------------------------------------
# run_scope_check
# ---------------------------------------------------------------------------

def test_run_scope_check_delegates_to_check_scope():
    cfg = ScopeConfig(allowed_namespaces=["prod"], allowed_paths=[])
    result = run_scope_check(cfg, "prod", ["secret/db"])
    assert not result.has_violations


def test_run_scope_check_returns_violations():
    cfg = ScopeConfig(allowed_namespaces=["staging"], allowed_paths=[])
    result = run_scope_check(cfg, "prod", ["secret/db"])
    assert result.has_violations


# ---------------------------------------------------------------------------
# echo_scope_results
# ---------------------------------------------------------------------------

def test_echo_scope_results_ok(capsys):
    result = ScopeResult(violations=[])
    echo_scope_results(result)
    captured = capsys.readouterr()
    assert "within permitted scope" in captured.out


def test_echo_scope_results_violations(capsys):
    result = ScopeResult(
        violations=[ScopeViolation("prod", "secret/x", "outside permitted scope")]
    )
    echo_scope_results(result)
    captured = capsys.readouterr()
    assert "scope violation" in captured.err
    assert "secret/x" in captured.err


# ---------------------------------------------------------------------------
# abort_on_scope_violation
# ---------------------------------------------------------------------------

def test_abort_on_scope_violation_no_violations_does_not_raise():
    result = ScopeResult(violations=[])
    abort_on_scope_violation(result)  # should not raise


def test_abort_on_scope_violation_raises_system_exit():
    result = ScopeResult(
        violations=[ScopeViolation("prod", "secret/x", "outside permitted scope")]
    )
    with pytest.raises(SystemExit):
        abort_on_scope_violation(result)
