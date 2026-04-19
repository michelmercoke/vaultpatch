"""Tests for vaultpatch.fetch."""
from unittest.mock import MagicMock, patch

import pytest

from vaultpatch.config import NamespaceConfig
from vaultpatch.fetch import FetchResult, fetch_secrets


@pytest.fixture()
def ns_cfg():
    return NamespaceConfig(
        name="prod",
        address="https://vault.example.com",
        mount="secret",
        token_env="VAULT_TOKEN",
    )


def _mock_client(secrets_by_path: dict) -> MagicMock:
    client = MagicMock()

    def read_secret_version(path, mount_point, raise_on_deleted_version):
        if path not in secrets_by_path:
            raise Exception(f"path not found: {path}")
        return {"data": {"data": secrets_by_path[path]}}

    client.secrets.kv.v2.read_secret_version.side_effect = read_secret_version
    return client


def test_fetch_returns_secrets(ns_cfg):
    client = _mock_client({"app/config": {"DB_URL": "postgres://localhost/db"}})
    result = fetch_secrets(ns_cfg, ["app/config"], client=client)
    assert result.success
    assert result.secrets["app/config"] == {"DB_URL": "postgres://localhost/db"}


def test_fetch_records_error_on_missing_path(ns_cfg):
    client = _mock_client({})
    result = fetch_secrets(ns_cfg, ["app/missing"], client=client)
    assert not result.success
    assert "app/missing" in result.errors


def test_fetch_partial_errors(ns_cfg):
    client = _mock_client({"app/config": {"KEY": "val"}})
    result = fetch_secrets(ns_cfg, ["app/config", "app/other"], client=client)
    assert not result.success
    assert "app/config" in result.secrets
    assert "app/other" in result.errors


def test_fetch_no_token_records_errors(ns_cfg, monkeypatch):
    monkeypatch.delenv("VAULT_TOKEN", raising=False)
    ns_cfg_no_token = NamespaceConfig(
        name="prod",
        address="https://vault.example.com",
        mount="secret",
        token_env="VAULT_TOKEN",
    )
    result = fetch_secrets(ns_cfg_no_token, ["app/config"])
    assert not result.success
    assert "app/config" in result.errors


def test_fetch_result_namespace(ns_cfg):
    client = _mock_client({})
    result = fetch_secrets(ns_cfg, [], client=client)
    assert result.namespace == "prod"
    assert result.success
