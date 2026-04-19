"""Tests for vaultpatch configuration loader."""

import os
import textwrap
from pathlib import Path

import pytest

from vaultpatch.config import NamespaceConfig, VaultPatchConfig


@pytest.fixture
def config_file(tmp_path: Path) -> Path:
    content = textwrap.dedent("""\
        default_mount: kv
        namespaces:
          - name: prod
            address: https://vault.prod.example.com
            token_env: VAULT_TOKEN_PROD
            mount: kv
          - name: staging
            address: https://vault.staging.example.com
            token_env: VAULT_TOKEN_STAGING
    """)
    cfg = tmp_path / "vaultpatch.yaml"
    cfg.write_text(content)
    return cfg


def test_load_config(config_file: Path):
    cfg = VaultPatchConfig.from_file(config_file)
    assert cfg.default_mount == "kv"
    assert len(cfg.namespaces) == 2


def test_namespace_fields(config_file: Path):
    cfg = VaultPatchConfig.from_file(config_file)
    prod = cfg.get_namespace("prod")
    assert prod is not None
    assert prod.address == "https://vault.prod.example.com"
    assert prod.token_env == "VAULT_TOKEN_PROD"
    assert prod.mount == "kv"


def test_namespace_inherits_default_mount(config_file: Path):
    cfg = VaultPatchConfig.from_file(config_file)
    staging = cfg.get_namespace("staging")
    assert staging is not None
    assert staging.mount == "kv"  # inherited from default_mount


def test_namespace_token_from_env(config_file: Path, monkeypatch):
    monkeypatch.setenv("VAULT_TOKEN_PROD", "s.supersecret")
    cfg = VaultPatchConfig.from_file(config_file)
    prod = cfg.get_namespace("prod")
    assert prod.token == "s.supersecret"


def test_missing_config_raises(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        VaultPatchConfig.from_file(tmp_path / "nonexistent.yaml")


def test_get_namespace_missing(config_file: Path):
    cfg = VaultPatchConfig.from_file(config_file)
    assert cfg.get_namespace("dev") is None
