"""Tests for vaultpatch.embargo_hook."""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from vaultpatch.embargo import EmbargoConfig, EmbargoResult, EmbargoViolation, EmbargoWindow
from vaultpatch.embargo_hook import abort_on_embargo, echo_embargo_results, run_embargo_check
from vaultpatch.cli_embargo import embargo_cmd

ACTIVE_START = "2099-01-01T00:00:00+00:00"
ACTIVE_END = "2099-12-31T23:59:59+00:00"
NOW = datetime(2099, 6, 15, tzinfo=timezone.utc)


@pytest.fixture
fn runner():
    return CliRunner()


def _active_config() -> EmbargoConfig:
    return EmbargoConfig(
        windows=[
            EmbargoWindow(
                label="freeze",
                path_pattern="secret/prod/*",
                start=ACTIVE_START,
                end=ACTIVE_END,
            )
        ]
    )


def test_run_embargo_check_delegates():
    config = _active_config()
    result = run_embargo_check(["secret/prod/db"], config, now=NOW)
    assert result.has_violations


def test_run_embargo_check_clean():
    config = _active_config()
    result = run_embargo_check(["secret/dev/db"], config, now=NOW)
    assert not result.has_violations


def test_echo_embargo_results_no_violations(capsys):
    result = EmbargoResult()
    echo_embargo_results(result)
    captured = capsys.readouterr()
    assert "no active embargoes" in captured.out


def test_echo_embargo_results_with_violations(capsys):
    v = EmbargoViolation(path="secret/prod/x", reason="embargoed by 'freeze'")
    result = EmbargoResult(violations=[v])
    echo_embargo_results(result)
    captured = capsys.readouterr()
    assert "secret/prod/x" in captured.err


def test_abort_on_embargo_raises_when_violations():
    v = EmbargoViolation(path="secret/prod/x", reason="embargoed")
    result = EmbargoResult(violations=[v])
    with pytest.raises(SystemExit):
        abort_on_embargo(result)


def test_abort_on_embargo_does_not_raise_when_clean():
    result = EmbargoResult()
    abort_on_embargo(result)  # should not raise


def test_cli_check_dry_run_does_not_abort():
    runner = CliRunner()
    result = runner.invoke(
        embargo_cmd,
        [
            "check",
            "secret/prod/db",
            "--path-pattern", "secret/prod/*",
            "--start", ACTIVE_START,
            "--end", ACTIVE_END,
            "--label", "freeze",
            "--dry-run",
            "--at", "2099-06-15T12:00:00+00:00",
        ],
    )
    assert result.exit_code == 0
