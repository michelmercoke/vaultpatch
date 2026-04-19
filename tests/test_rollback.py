"""Tests for vaultpatch.rollback."""
from unittest.mock import MagicMock, patch

import pytest

from vaultpatch.rollback import rollback_path, RollbackResult
from vaultpatch.config import NamespaceConfig


@pytest.fixture
def ns_cfg():
    return NamespaceConfig(
        name="prod",
        address="https://vault.example.com",
        token="root",
        mount="secret",
        paths=["db/creds"],
    )


def _mock_client(current_data: dict):
    client = MagicMock()
    client.secrets.kv.v2.read_secret_version.return_value = {
        "data": {"data": current_data}
    }
    return client


def test_rollback_reverts_changed_keys(ns_cfg):
    snapshot = {"user": "admin", "pass": "old"}
    current = {"user": "admin", "pass": "new"}
    client = _mock_client(current)
    with patch("vaultpatch.rollback._make_client", return_value=client):
        result = rollback_path(ns_cfg, "db/creds", snapshot)
    assert result.success
    assert "pass" in result.reverted_keys
    client.secrets.kv.v2.create_or_update_secret.assert_called_once()


def test_rollback_no_changes(ns_cfg):
    snapshot = {"user": "admin"}
    client = _mock_client({"user": "admin"})
    with patch("vaultpatch.rollback._make_client", return_value=client):
        result = rollback_path(ns_cfg, "db/creds", snapshot)
    assert result.success
    assert result.reverted_keys == []
    client.secrets.kv.v2.create_or_update_secret.assert_not_called()


def test_rollback_read_error(ns_cfg):
    client = MagicMock()
    client.secrets.kv.v2.read_secret_version.side_effect = Exception("forbidden")
    with patch("vaultpatch.rollback._make_client", return_value=client):
        result = rollback_path(ns_cfg, "db/creds", {})
    assert not result.success
    assert "forbidden" in result.error


def test_rollback_write_error(ns_cfg):
    snapshot = {"pass": "old"}
    client = _mock_client({"pass": "new"})
    client.secrets.kv.v2.create_or_update_secret.side_effect = Exception("read-only")
    with patch("vaultpatch.rollback._make_client", return_value=client):
        result = rollback_path(ns_cfg, "db/creds", snapshot)
    assert not result.success
    assert "read-only" in result.error
