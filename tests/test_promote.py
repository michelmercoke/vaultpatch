"""Tests for vaultpatch.promote."""
from unittest.mock import MagicMock, patch

import pytest

from vaultpatch.config import NamespaceConfig
from vaultpatch.promote import promote_path, promote_paths


@pytest.fixture()
def src_cfg() -> NamespaceConfig:
    return NamespaceConfig(name="dev", address="http://vault:8200", token="src-tok", mount="secret", namespace=None)


@pytest.fixture()
def tgt_cfg() -> NamespaceConfig:
    return NamespaceConfig(name="staging", address="http://vault:8200", token="tgt-tok", mount="secret", namespace=None)


def _mock_client(data=None, read_exc=None, write_exc=None):
    client = MagicMock()
    if read_exc:
        client.secrets.kv.v2.read_secret_version.side_effect = read_exc
    else:
        client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": data or {"key": "value"}}
        }
    if write_exc:
        client.secrets.kv.v2.create_or_update_secret.side_effect = write_exc
    return client


def test_promote_success(src_cfg, tgt_cfg):
    mock = _mock_client(data={"foo": "bar"})
    with patch("vaultpatch.promote._make_client", return_value=mock):
        result = promote_path(src_cfg, tgt_cfg, "myapp/config")
    assert result.success
    assert result.error is None
    assert result.path == "myapp/config"


def test_promote_read_error(src_cfg, tgt_cfg):
    mock = _mock_client(read_exc=Exception("not found"))
    with patch("vaultpatch.promote._make_client", return_value=mock):
        result = promote_path(src_cfg, tgt_cfg, "missing/path")
    assert not result.success
    assert "read error" in result.error


def test_promote_write_error(src_cfg, tgt_cfg):
    mock = _mock_client(write_exc=Exception("permission denied"))
    with patch("vaultpatch.promote._make_client", return_value=mock):
        result = promote_path(src_cfg, tgt_cfg, "myapp/config")
    assert not result.success
    assert "write error" in result.error


def test_promote_dry_run_skips_write(src_cfg, tgt_cfg):
    mock = _mock_client(data={"x": "y"})
    with patch("vaultpatch.promote._make_client", return_value=mock):
        result = promote_path(src_cfg, tgt_cfg, "myapp/config", dry_run=True)
    assert result.success
    mock.secrets.kv.v2.create_or_update_secret.assert_not_called()


def test_promote_paths_returns_all(src_cfg, tgt_cfg):
    mock = _mock_client()
    with patch("vaultpatch.promote._make_client", return_value=mock):
        results = promote_paths(src_cfg, tgt_cfg, ["a", "b", "c"])
    assert len(results) == 3
    assert all(r.success for r in results)
