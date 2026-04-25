"""Tests for vaultpatch.watermark."""
from __future__ import annotations

import os

import pytest

from vaultpatch.watermark import (
    WatermarkConfig,
    build_watermark,
    stamp_secret,
    strip_watermark,
    _DEFAULT_KEY,
)


# ---------------------------------------------------------------------------
# WatermarkConfig
# ---------------------------------------------------------------------------

def test_from_dict_defaults():
    cfg = WatermarkConfig.from_dict({})
    assert cfg.enabled is True
    assert cfg.key == _DEFAULT_KEY
    assert cfg.include_user is True
    assert cfg.include_timestamp is True
    assert cfg.extra == {}


def test_from_dict_custom_key():
    cfg = WatermarkConfig.from_dict({"key": "__wm", "enabled": False})
    assert cfg.key == "__wm"
    assert cfg.enabled is False


# ---------------------------------------------------------------------------
# build_watermark
# ---------------------------------------------------------------------------

def test_build_watermark_disabled_returns_none():
    cfg = WatermarkConfig(enabled=False)
    assert build_watermark(cfg) is None


def test_build_watermark_contains_user(monkeypatch):
    monkeypatch.setenv("VAULTPATCH_USER", "alice")
    cfg = WatermarkConfig(include_timestamp=False)
    wm = build_watermark(cfg)
    assert wm is not None
    assert "user=alice" in wm


def test_build_watermark_contains_timestamp():
    cfg = WatermarkConfig(include_user=False)
    wm = build_watermark(cfg)
    assert wm is not None
    assert "ts=" in wm


def test_build_watermark_extra_fields():
    cfg = WatermarkConfig(include_user=False, include_timestamp=False, extra={"env": "prod"})
    wm = build_watermark(cfg)
    assert wm == "env=prod"


def test_build_watermark_falls_back_to_env_user(monkeypatch):
    monkeypatch.delenv("VAULTPATCH_USER", raising=False)
    monkeypatch.setenv("USER", "bob")
    cfg = WatermarkConfig(include_timestamp=False)
    wm = build_watermark(cfg)
    assert "user=bob" in wm


# ---------------------------------------------------------------------------
# stamp_secret
# ---------------------------------------------------------------------------

def test_stamp_secret_injects_key():
    cfg = WatermarkConfig()
    result = stamp_secret({"api_key": "s3cr3t"}, cfg, watermark="user=ci|ts=2024-01-01T00:00:00+00:00")
    assert cfg.key in result
    assert result["api_key"] == "s3cr3t"


def test_stamp_secret_disabled_leaves_data_unchanged():
    cfg = WatermarkConfig(enabled=False)
    data = {"foo": "bar"}
    result = stamp_secret(data, cfg)
    assert result == data
    assert cfg.key not in result


def test_stamp_secret_does_not_mutate_original():
    cfg = WatermarkConfig()
    data = {"x": "1"}
    stamp_secret(data, cfg, watermark="wm")
    assert cfg.key not in data


# ---------------------------------------------------------------------------
# strip_watermark
# ---------------------------------------------------------------------------

def test_strip_watermark_removes_key():
    cfg = WatermarkConfig()
    data = {"secret": "val", cfg.key: "user=ci"}
    result = strip_watermark(data, cfg)
    assert cfg.key not in result
    assert result["secret"] == "val"


def test_strip_watermark_noop_when_absent():
    cfg = WatermarkConfig()
    data = {"a": "b"}
    assert strip_watermark(data, cfg) == data
