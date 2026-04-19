"""Tests for vaultpatch.schema."""
import pytest
from vaultpatch.schema import SchemaRule, SchemaConfig, check_secrets


@pytest.fixture
def simple_schema():
    return SchemaConfig(rules=[
        SchemaRule(key_pattern="db_password", required=True, min_length=8, max_length=64),
        SchemaRule(key_pattern="api_*", regex=r"[A-Za-z0-9_\-]+"),
    ])


def test_valid_secrets_pass(simple_schema):
    secrets = {"db_password": "supersecret", "api_key": "abc123"}
    result = check_secrets(secrets, simple_schema)
    assert result.valid
    assert result.errors == []


def test_required_key_missing():
    schema = SchemaConfig(rules=[SchemaRule(key_pattern="db_password", required=True)])
    result = check_secrets({"other_key": "value"}, schema)
    assert not result.valid
    assert any("required" in e for e in result.errors)


def test_min_length_violation(simple_schema):
    secrets = {"db_password": "short", "api_key": "abc"}
    result = check_secrets(secrets, simple_schema)
    assert not result.valid
    assert any("too short" in e for e in result.errors)


def test_max_length_violation():
    schema = SchemaConfig(rules=[SchemaRule(key_pattern="token", max_length=10)])
    secrets = {"token": "a" * 20}
    result = check_secrets(secrets, schema)
    assert not result.valid
    assert any("too long" in e for e in result.errors)


def test_regex_violation(simple_schema):
    secrets = {"db_password": "validpass", "api_key": "bad value!"}
    result = check_secrets(secrets, simple_schema)
    assert not result.valid
    assert any("does not match pattern" in e for e in result.errors)


def test_wildcard_key_pattern_matches_multiple():
    schema = SchemaConfig(rules=[SchemaRule(key_pattern="env_*", min_length=3)])
    secrets = {"env_prod": "ok", "env_dev": "x", "other": "ignored"}
    result = check_secrets(secrets, schema)
    assert not result.valid
    assert len(result.errors) == 1
    assert "env_dev" in result.errors[0]


def test_from_dict():
    data = {
        "rules": [
            {"key_pattern": "secret", "required": True, "min_length": 5, "regex": r"\w+"}
        ]
    }
    schema = SchemaConfig.from_dict(data)
    assert len(schema.rules) == 1
    rule = schema.rules[0]
    assert rule.key_pattern == "secret"
    assert rule.required is True
    assert rule.min_length == 5


def test_empty_schema_always_passes():
    schema = SchemaConfig(rules=[])
    result = check_secrets({"any_key": "any_value"}, schema)
    assert result.valid
