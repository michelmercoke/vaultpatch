"""Tests for vaultpatch.cascade_hook."""
import pytest
from click.testing import CliRunner

from vaultpatch.cascade import CascadeResult, CascadeRule, CascadeViolation
from vaultpatch.cascade_hook import (
    abort_on_cascade_failure,
    echo_cascade_results,
    run_cascade,
)

SOURCE = "secret/prod/db"


def test_run_cascade_delegates():
    rule = CascadeRule(source=SOURCE, targets=["secret/staging/db"])
    result = run_cascade(SOURCE, {"key": "val"}, [rule])
    assert result.total_propagations == 1


def test_echo_no_propagations(capsys):
    result = CascadeResult()
    echo_cascade_results(result)
    captured = capsys.readouterr()
    assert "no propagations" in captured.out


def test_echo_propagations_listed(capsys):
    result = CascadeResult()
    result.propagations["secret/staging/db"] = {"password": "x", "user": "y"}
    echo_cascade_results(result)
    captured = capsys.readouterr()
    assert "secret/staging/db" in captured.out
    assert "password" in captured.out


def test_echo_violations_to_stderr(capsys):
    result = CascadeResult()
    result.violations.append(
        CascadeViolation(source=SOURCE, target="secret/dev/db", key="pw", reason="blank")
    )
    echo_cascade_results(result)
    captured = capsys.readouterr()
    assert "cascade warning" in captured.err


def test_abort_on_cascade_failure_raises_when_violations():
    result = CascadeResult()
    result.violations.append(
        CascadeViolation(source=SOURCE, target="t", key="k", reason="blank")
    )
    with pytest.raises(SystemExit):
        abort_on_cascade_failure(result)


def test_abort_on_cascade_failure_passes_when_clean():
    result = CascadeResult()
    result.propagations["secret/staging/db"] = {"key": "val"}
    abort_on_cascade_failure(result)  # should not raise
