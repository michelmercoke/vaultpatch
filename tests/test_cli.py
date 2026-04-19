"""Tests for the vaultpatch CLI commands."""

import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock

from vaultpatch.cli import cli
from vaultpatch.fetch import FetchResult
from vaultpatch.compare import CompareResult
from vaultpatch.patch import PatchResult
from vaultpatch.diff import SecretDiff


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def mock_cfg(tmp_path):
    cfg_file = tmp_path / "vaultpatch.yaml"
    cfg_file.write_text(
        "defaults:\n  mount: secret\nnamespaces:\n  - name: dev\n    address: http://localhost:8200\n    token: root\n"
    )
    return str(cfg_file)


def _make_compare(diffs=None):
    diffs = diffs or []
    cr = MagicMock(spec=CompareResult)
    cr.diffs = diffs
    cr.has_changes.return_value = bool(diffs)
    cr.total_changes.return_value = len(diffs)
    return cr


def test_diff_no_changes(runner, mock_cfg):
    with patch("vaultpatch.cli.fetch_secrets") as mock_fetch, \
         patch("vaultpatch.cli.compare_results") as mock_compare:
        mock_fetch.return_value = FetchResult(secrets={"k": "v"}, error=None)
        mock_compare.return_value = _make_compare()

        result = runner.invoke(cli, ["diff", "-c", mock_cfg])

        assert result.exit_code == 0
        assert "No changes detected" in result.output


def test_diff_with_changes(runner, mock_cfg):
    diff = MagicMock(spec=SecretDiff)
    diff.key = "password"
    diff.label.return_value = "[changed]"

    with patch("vaultpatch.cli.fetch_secrets") as mock_fetch, \
         patch("vaultpatch.cli.compare_results") as mock_compare:
        mock_fetch.return_value = FetchResult(secrets={"password": "new"}, error=None)
        mock_compare.return_value = _make_compare([diff])

        result = runner.invoke(cli, ["diff", "-c", mock_cfg])

        assert result.exit_code == 0
        assert "password" in result.output
        assert "Total changes: 1" in result.output


def test_diff_fetch_error(runner, mock_cfg):
    with patch("vaultpatch.cli.fetch_secrets") as mock_fetch:
        mock_fetch.return_value = FetchResult(secrets={}, error="connection refused")

        result = runner.invoke(cli, ["diff", "-c", mock_cfg])

        assert "connection refused" in result.output


def test_apply_dry_run(runner, mock_cfg):
    with patch("vaultpatch.cli.fetch_secrets") as mock_fetch, \
         patch("vaultpatch.cli.compare_results") as mock_compare:
        mock_fetch.return_value = FetchResult(secrets={"x": "1"}, error=None)
        mock_compare.return_value = _make_compare([MagicMock()])

        result = runner.invoke(cli, ["apply", "-c", mock_cfg, "--dry-run"])

        assert result.exit_code == 0
        assert "Dry run" in result.output


def test_apply_success(runner, mock_cfg):
    with patch("vaultpatch.cli.fetch_secrets") as mock_fetch, \
         patch("vaultpatch.cli.compare_results") as mock_compare, \
         patch("vaultpatch.cli.apply_diffs") as mock_apply:
        mock_fetch.return_value = FetchResult(secrets={"x": "1"}, error=None)
        mock_compare.return_value = _make_compare([MagicMock()])
        mock_apply.return_value = PatchResult(success=True, error=None)

        result = runner.invoke(cli, ["apply", "-c", mock_cfg])

        assert result.exit_code == 0
        assert "OK" in result.output
