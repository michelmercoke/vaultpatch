"""Tests for vaultpatch.template."""

from __future__ import annotations

import pytest

from vaultpatch.template import TemplateError, TemplateResult, render_secrets


_ENV = {
    "APP_ENV": "production",
    "DB_PASS": "s3cr3t",
    "REGION": "eu-west-1",
}


def test_no_placeholders_returned_unchanged():
    result = render_secrets({"key": "plain-value"}, env=_ENV)
    assert result.success
    assert result.rendered["key"] == "plain-value"


def test_single_placeholder_resolved():
    result = render_secrets({"env": "${APP_ENV}"}, env=_ENV)
    assert result.success
    assert result.rendered["env"] == "production"


def test_multiple_placeholders_in_one_value():
    result = render_secrets({"dsn": "db://${REGION}/${DB_PASS}"}, env=_ENV)
    assert result.success
    assert result.rendered["dsn"] == "db://eu-west-1/s3cr3t"


def test_default_used_when_var_absent():
    result = render_secrets({"tier": "${MISSING_VAR:fallback}"}, env=_ENV)
    assert result.success
    assert result.rendered["tier"] == "fallback"


def test_error_when_var_absent_and_no_default():
    result = render_secrets({"secret": "${UNDEFINED_VAR}"}, env=_ENV)
    assert not result.success
    assert len(result.errors) == 1
    err = result.errors[0]
    assert isinstance(err, TemplateError)
    assert err.key == "secret"
    assert "UNDEFINED_VAR" in err.placeholder


def test_placeholder_left_unchanged_on_error():
    result = render_secrets({"x": "${NO_DEFAULT}"}, env={})
    assert result.rendered["x"] == "${NO_DEFAULT}"


def test_multiple_keys_independent_errors():
    secrets = {
        "good": "${APP_ENV}",
        "bad": "${MISSING}",
    }
    result = render_secrets(secrets, env=_ENV)
    assert not result.success
    assert result.rendered["good"] == "production"
    assert len(result.errors) == 1
    assert result.errors[0].key == "bad"


def test_empty_secrets_returns_empty_result():
    result = render_secrets({}, env=_ENV)
    assert result.success
    assert result.rendered == {}


def test_default_env_falls_back_to_os_environ(monkeypatch):
    monkeypatch.setenv("MY_SECRET_KEY", "from_os")
    result = render_secrets({"val": "${MY_SECRET_KEY}"})
    assert result.success
    assert result.rendered["val"] == "from_os"
