"""Tests for vaultpatch.access and vaultpatch.access_hook."""
from __future__ import annotations

import pytest
from click.testing import CliRunner

from vaultpatch.access import AccessRule, AccessViolation, check_access
from vaultpatch.access_hook import (
    abort_on_access_denied,
    echo_access_results,
    run_access_check,
)


# ---------------------------------------------------------------------------
# check_access
# ---------------------------------------------------------------------------

def _rules():
    return [
        AccessRule(namespace="prod", path="secret/app/*", allow=True),
        AccessRule(namespace="prod", path="secret/infra/*", allow=False),
        AccessRule(namespace="staging", path="*", allow=True),
    ]


def test_allowed_path_passes():
    result = check_access("prod", ["secret/app/db"], _rules())
    assert result.allowed
    assert result.violations == []


def test_denied_path_produces_violation():
    result = check_access("prod", ["secret/infra/network"], _rules())
    assert not result.allowed
    assert len(result.violations) == 1
    v = result.violations[0]
    assert v.namespace == "prod"
    assert v.path == "secret/infra/network"


def test_multiple_paths_mixed():
    paths = ["secret/app/db", "secret/infra/network", "secret/app/cache"]
    result = check_access("prod", paths, _rules())
    assert not result.allowed
    assert len(result.violations) == 1
    assert result.violations[0].path == "secret/infra/network"


def test_no_matching_rule_uses_default_deny():
    result = check_access("dev", ["secret/unknown"], _rules(), default_allow=False)
    assert not result.allowed


def test_no_matching_rule_uses_default_allow():
    result = check_access("dev", ["secret/unknown"], _rules(), default_allow=True)
    assert result.allowed


def test_wildcard_namespace_matches():
    rules = [AccessRule(namespace="*", path="secret/*", allow=True)]
    result = check_access("anything", ["secret/foo"], rules)
    assert result.allowed


def test_violation_str():
    v = AccessViolation("prod", "secret/infra/x", "denied by rule 'prod:secret/infra/*'")
    assert "prod" in str(v)
    assert "secret/infra/x" in str(v)


# ---------------------------------------------------------------------------
# access_hook
# ---------------------------------------------------------------------------

def test_run_access_check_delegates():
    rules = [AccessRule(namespace="ns", path="secret/*", allow=False)]
    result = run_access_check("ns", ["secret/key"], rules)
    assert not result.allowed


def test_echo_access_results_allowed(capsys):
    from vaultpatch.access import AccessResult
    result = AccessResult()
    echo_access_results(result)
    captured = capsys.readouterr()
    assert "passed" in captured.out


def test_echo_access_results_denied(capsys):
    result = check_access("prod", ["secret/infra/x"], _rules())
    echo_access_results(result)
    captured = capsys.readouterr()
    assert "DENIED" in captured.out


def test_abort_on_access_denied_raises():
    result = check_access("prod", ["secret/infra/x"], _rules())
    with pytest.raises(SystemExit) as exc_info:
        abort_on_access_denied(result)
    assert exc_info.value.code == 1


def test_abort_on_access_allowed_does_not_raise():
    result = check_access("prod", ["secret/app/db"], _rules())
    abort_on_access_denied(result)  # should not raise
