"""Tests for vaultpatch/masking.py and masking_hook.py."""
from __future__ import annotations

import pytest

from vaultpatch.diff import SecretDiff
from vaultpatch.masking import MaskingConfig, MaskResult, mask_value, mask_secrets
from vaultpatch.masking_hook import apply_masking_to_diffs, echo_masked_diffs


# ---------------------------------------------------------------------------
# MaskingConfig.from_dict
# ---------------------------------------------------------------------------

def test_from_dict_defaults():
    cfg = MaskingConfig.from_dict({})
    assert cfg.enabled is True
    assert cfg.mask_string == "***"
    assert cfg.visible_suffix_chars == 4
    assert cfg.always_full_mask_keys == []


def test_from_dict_custom_values():
    cfg = MaskingConfig.from_dict({
        "enabled": False,
        "mask_string": "REDACTED",
        "visible_suffix_chars": 2,
        "always_full_mask_keys": ["root_token"],
    })
    assert cfg.enabled is False
    assert cfg.mask_string == "REDACTED"
    assert cfg.visible_suffix_chars == 2
    assert "root_token" in cfg.always_full_mask_keys


# ---------------------------------------------------------------------------
# mask_value
# ---------------------------------------------------------------------------

def test_mask_value_shows_suffix():
    cfg = MaskingConfig(visible_suffix_chars=4)
    result = mask_value("db_pass", "supersecret", cfg)
    assert result.masked == "***cret"
    assert result.fully_masked is False


def test_mask_value_fully_masked_when_zero_suffix():
    cfg = MaskingConfig(visible_suffix_chars=0)
    result = mask_value("db_pass", "supersecret", cfg)
    assert result.masked == "***"
    assert result.fully_masked is True


def test_mask_value_fully_masked_for_always_full_key():
    cfg = MaskingConfig(always_full_mask_keys=["root_token"], visible_suffix_chars=4)
    result = mask_value("root_token", "abcdefgh", cfg)
    assert result.masked == "***"
    assert result.fully_masked is True


def test_mask_value_short_value_fully_masked():
    cfg = MaskingConfig(visible_suffix_chars=4)
    result = mask_value("pin", "123", cfg)
    assert result.masked == "***"
    assert result.fully_masked is True


def test_mask_value_disabled_returns_original():
    cfg = MaskingConfig(enabled=False)
    result = mask_value("key", "plaintext", cfg)
    assert result.masked == "plaintext"
    assert result.fully_masked is False


def test_mask_value_none_returns_none():
    cfg = MaskingConfig()
    result = mask_value("key", None, cfg)
    assert result.masked is None


# ---------------------------------------------------------------------------
# mask_secrets
# ---------------------------------------------------------------------------

def test_mask_secrets_returns_masked_dict():
    cfg = MaskingConfig(visible_suffix_chars=2)
    secrets = {"password": "hunter2", "user": "admin"}
    result = mask_secrets(secrets, cfg)
    assert result["password"] == "***r2"
    assert result["user"] == "***in"


# ---------------------------------------------------------------------------
# apply_masking_to_diffs
# ---------------------------------------------------------------------------

def test_apply_masking_to_diffs_masks_new_and_old():
    cfg = MaskingConfig(visible_suffix_chars=3)
    diffs = [
        SecretDiff(path="secret/app", key="pass", old_value="oldpassword", new_value="newpassword"),
    ]
    masked = apply_masking_to_diffs(diffs, cfg)
    assert masked[0].old_value == "***ord"
    assert masked[0].new_value == "***ord"


def test_apply_masking_preserves_none_values():
    cfg = MaskingConfig()
    diffs = [
        SecretDiff(path="secret/app", key="token", old_value=None, new_value="newtoken"),
    ]
    masked = apply_masking_to_diffs(diffs, cfg)
    assert masked[0].old_value is None
    assert masked[0].new_value is not None


# ---------------------------------------------------------------------------
# echo_masked_diffs (smoke test)
# ---------------------------------------------------------------------------

def test_echo_masked_diffs_runs_without_error(capsys):
    cfg = MaskingConfig(visible_suffix_chars=2)
    diffs = [
        SecretDiff(path="secret/app", key="added_key", old_value=None, new_value="newvalue"),
        SecretDiff(path="secret/app", key="removed_key", old_value="oldvalue", new_value=None),
        SecretDiff(path="secret/app", key="changed_key", old_value="aaa", new_value="bbb"),
    ]
    echo_masked_diffs(diffs, cfg)
    captured = capsys.readouterr()
    assert "added_key" in captured.out
    assert "removed_key" in captured.out
    assert "changed_key" in captured.out
