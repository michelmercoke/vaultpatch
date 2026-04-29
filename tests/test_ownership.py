"""Tests for vaultpatch.ownership."""
import pytest

from vaultpatch.diff import SecretDiff
from vaultpatch.ownership import (
    OwnershipConfig,
    OwnershipRule,
    check_ownership,
)


def _diff(path: str, key: str = "api_key") -> SecretDiff:
    return SecretDiff(path=path, key=key, old_value="old", new_value="new")


@pytest.fixture
def _rules() -> OwnershipConfig:
    return OwnershipConfig.from_dict(
        {
            "require_owner": True,
            "rules": [
                {"path": "secret/prod/*", "owner": "alice", "team": "platform"},
                {"path": "secret/staging/*", "owner": "bob"},
            ],
        }
    )


def test_owned_path_produces_assignment(_rules):
    diffs = {"secret/prod/db": [_diff("secret/prod/db")]}
    result = check_ownership(diffs, _rules)
    assert not result.has_violations
    assert any(a[0] == "secret/prod/db" and a[1] == "alice" for a in result.assignments)


def test_owned_path_includes_team(_rules):
    diffs = {"secret/prod/cache": [_diff("secret/prod/cache")]}
    result = check_ownership(diffs, _rules)
    assert result.assignments[0][2] == "platform"


def test_owned_path_without_team_has_none(_rules):
    diffs = {"secret/staging/app": [_diff("secret/staging/app")]}
    result = check_ownership(diffs, _rules)
    assert result.assignments[0][2] is None


def test_unowned_path_produces_violation(_rules):
    diffs = {"secret/dev/service": [_diff("secret/dev/service")]}
    result = check_ownership(diffs, _rules)
    assert result.has_violations
    assert result.violations[0].path == "secret/dev/service"
    assert "no owner" in result.violations[0].message


def test_violation_str(_rules):
    diffs = {"secret/orphan/key": [_diff("secret/orphan/key")]}
    result = check_ownership(diffs, _rules)
    assert "[ownership]" in str(result.violations[0])
    assert "secret/orphan/key" in str(result.violations[0])


def test_require_owner_false_allows_unowned_path():
    cfg = OwnershipConfig.from_dict({"require_owner": False, "rules": []})
    diffs = {"secret/anywhere": [_diff("secret/anywhere")]}
    result = check_ownership(diffs, cfg)
    assert not result.has_violations


def test_empty_diffs_skipped(_rules):
    diffs = {"secret/prod/empty": []}
    result = check_ownership(diffs, _rules)
    assert not result.has_violations
    assert not result.assignments


def test_multiple_paths_mixed_ownership(_rules):
    diffs = {
        "secret/prod/svc": [_diff("secret/prod/svc")],
        "secret/unknown/svc": [_diff("secret/unknown/svc")],
    }
    result = check_ownership(diffs, _rules)
    assert len(result.assignments) == 1
    assert len(result.violations) == 1


def test_from_dict_defaults():
    cfg = OwnershipConfig.from_dict({})
    assert cfg.require_owner is True
    assert cfg.rules == []
