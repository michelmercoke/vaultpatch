"""Tests for vaultpatch.notify."""
from unittest.mock import MagicMock, patch

import pytest

from vaultpatch.diff import SecretDiff
from vaultpatch.notify import NotifyConfig, NotifyResult, _build_payload, send_notification
from vaultpatch.report import Report, ReportEntry


@pytest.fixture()
def _diff():
    return SecretDiff(key="db_pass", old="old", new="new")


@pytest.fixture()
def sample_report(_diff):
    r = Report()
    r.add("prod", "secret/app", [_diff])
    return r


def test_build_payload_contains_mode(sample_report):
    payload = _build_payload(sample_report, "diff", None)
    assert "diff" in payload["text"]


def test_build_payload_includes_mention(sample_report):
    payload = _build_payload(sample_report, "apply", "@oncall")
    assert "@oncall" in payload["text"]


def test_build_payload_lists_paths(sample_report):
    payload = _build_payload(sample_report, "diff", None)
    assert "secret/app" in payload["text"]


def test_send_notification_skips_empty_report():
    r = Report()
    cfg = NotifyConfig(webhook_url="http://example.com/hook")
    result = send_notification(r, "diff", cfg)
    assert result.sent is False
    assert result.status_code is None


def test_send_notification_posts_payload(sample_report):
    cfg = NotifyConfig(webhook_url="http://example.com/hook")
    mock_resp = MagicMock(status_code=200)
    with patch("vaultpatch.notify.httpx.post", return_value=mock_resp) as mock_post:
        result = send_notification(sample_report, "diff", cfg)
    assert result.sent is True
    assert result.status_code == 200
    mock_post.assert_called_once()


def test_send_notification_captures_error(sample_report):
    cfg = NotifyConfig(webhook_url="http://example.com/hook")
    with patch("vaultpatch.notify.httpx.post", side_effect=Exception("timeout")):
        result = send_notification(sample_report, "apply", cfg)
    assert result.sent is False
    assert "timeout" in result.error


def test_notify_config_from_env(monkeypatch):
    monkeypatch.setenv("VAULTPATCH_WEBHOOK_URL", "http://hooks.example.com")
    monkeypatch.setenv("VAULTPATCH_NOTIFY_MENTION", "@team")
    cfg = NotifyConfig.from_env()
    assert cfg is not None
    assert cfg.webhook_url == "http://hooks.example.com"
    assert cfg.mention == "@team"


def test_notify_config_from_env_missing(monkeypatch):
    monkeypatch.delenv("VAULTPATCH_WEBHOOK_URL", raising=False)
    assert NotifyConfig.from_env() is None
