"""Tests for vaultpatch.cascade."""
import pytest

from vaultpatch.cascade import (
    CascadeRule,
    build_cascade,
    rules_from_dict,
)


SOURCE = "secret/prod/db"
TARGETS = ["secret/staging/db", "secret/dev/db"]


@pytest.fixture()
def rule_all_keys():
    return CascadeRule(source=SOURCE, targets=TARGETS)


@pytest.fixture()
def rule_specific_keys():
    return CascadeRule(source=SOURCE, targets=TARGETS, keys=["password"])


def test_propagates_all_keys_when_no_filter(rule_all_keys):
    secrets = {"password": "s3cr3t", "user": "admin"}
    result = build_cascade(SOURCE, secrets, [rule_all_keys])
    assert result.total_propagations == 4  # 2 keys x 2 targets
    assert result.propagations["secret/staging/db"]["password"] == "s3cr3t"
    assert result.propagations["secret/dev/db"]["user"] == "admin"


def test_propagates_only_specified_keys(rule_specific_keys):
    secrets = {"password": "s3cr3t", "user": "admin"}
    result = build_cascade(SOURCE, secrets, [rule_specific_keys])
    assert "password" in result.propagations["secret/staging/db"]
    assert "user" not in result.propagations.get("secret/staging/db", {})


def test_blank_value_records_violation(rule_all_keys):
    secrets = {"password": ""}
    result = build_cascade(SOURCE, secrets, [rule_all_keys])
    assert result.has_violations
    assert result.violations[0].key == "password"
    assert "blank" in result.violations[0].reason


def test_non_matching_source_produces_no_result():
    rule = CascadeRule(source="secret/other", targets=TARGETS)
    result = build_cascade(SOURCE, {"key": "val"}, [rule])
    assert result.total_propagations == 0
    assert not result.has_violations


def test_multiple_rules_applied_independently():
    rule_a = CascadeRule(source=SOURCE, targets=["secret/staging/db"], keys=["password"])
    rule_b = CascadeRule(source=SOURCE, targets=["secret/dev/db"], keys=["user"])
    secrets = {"password": "pw", "user": "admin"}
    result = build_cascade(SOURCE, secrets, [rule_a, rule_b])
    assert "password" in result.propagations["secret/staging/db"]
    assert "user" in result.propagations["secret/dev/db"]
    assert "user" not in result.propagations.get("secret/staging/db", {})


def test_rules_from_dict_parses_correctly():
    raw = [
        {"source": "secret/prod/db", "targets": ["secret/staging/db"], "keys": ["password"]},
        {"source": "secret/prod/api", "targets": ["secret/dev/api"]},
    ]
    rules = rules_from_dict(raw)
    assert len(rules) == 2
    assert rules[0].source == "secret/prod/db"
    assert rules[0].keys == ["password"]
    assert rules[1].keys is None


def test_violation_str():
    from vaultpatch.cascade import CascadeViolation
    v = CascadeViolation(source="s", target="t", key="k", reason="blank value cannot be cascaded")
    assert "s -> t" in str(v)
    assert "k" in str(v)
