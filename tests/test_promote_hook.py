"""Tests for vaultpatch.promote_hook."""
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from vaultpatch.promote import PromoteResult
from vaultpatch.promote_hook import echo_promote_results, run_promote


def _result(path, success, error=None):
    return PromoteResult(source="dev", target="staging", path=path, success=success, error=error)


def test_run_promote_delegates(tmp_path):
    cfg = MagicMock()
    cfg.get_namespace.side_effect = lambda n: MagicMock(name=n)
    results = [_result("a", True)]
    with patch("vaultpatch.promote_hook.promote_paths", return_value=results) as mock_pp:
        out = run_promote(cfg, "dev", "staging", ["a"])
    mock_pp.assert_called_once()
    assert out == results


def test_echo_promote_results_success(capsys):
    results = [_result("a/b", True), _result("c/d", True)]
    echo_promote_results(results)
    captured = capsys.readouterr()
    assert "Promoted 2" in captured.out
    assert "0 failure" in captured.out


def test_echo_promote_results_failure(capsys):
    results = [_result("a/b", False, error="write error: boom")]
    echo_promote_results(results)
    captured = capsys.readouterr()
    assert "Promoted 0" in captured.out
    assert "1 failure" in captured.out


def test_echo_promote_dry_run_prefix(capsys):
    results = [_result("x/y", True)]
    echo_promote_results(results, dry_run=True)
    captured = capsys.readouterr()
    assert "[dry-run]" in captured.out
