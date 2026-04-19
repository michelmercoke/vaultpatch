"""Tests for vaultpatch.filter."""
import pytest
from vaultpatch.diff import SecretDiff
from vaultpatch.filter import FilterOptions, filter_diffs, filter_by_prefix, filter_by_key


def _diff(path: str, key: str, old=None, new=None) -> SecretDiff:
    return SecretDiff(path=path, key=key, old_value=old, new_value=new)


@pytest.fixture
def sample_diffs():
    return [
        _diff("secret/app/db", "password", old="old", new="new"),
        _diff("secret/app/db", "host", old=None, new="localhost"),
        _diff("secret/infra/tls", "cert", old="abc", new=None),
        _diff("secret/infra/tls", "key", old="x", new="y"),
    ]


def test_filter_by_prefix(sample_diffs):
    result = filter_by_prefix(sample_diffs, "secret/app")
    assert len(result) == 2
    assert all(d.path.startswith("secret/app") for d in result)


def test_filter_by_key_exact(sample_diffs):
    result = filter_by_key(sample_diffs, "password")
    assert len(result) == 1
    assert result[0].key == "password"


def test_filter_by_key_wildcard(sample_diffs):
    result = filter_by_key(sample_diffs, "*key*")
    assert len(result) == 1
    assert result[0].key == "key"


def test_filter_diffs_change_type_added(sample_diffs):
    opts = FilterOptions(change_types=["added"])
    result = filter_diffs(sample_diffs, opts)
    assert all(d.is_added() for d in result)
    assert len(result) == 1


def test_filter_diffs_change_type_removed(sample_diffs):
    opts = FilterOptions(change_types=["removed"])
    result = filter_diffs(sample_diffs, opts)
    assert all(d.is_removed() for d in result)
    assert len(result) == 1


def test_filter_diffs_combined(sample_diffs):
    opts = FilterOptions(path_prefix="secret/app", change_types=["added", "changed"])
    result = filter_diffs(sample_diffs, opts)
    assert len(result) == 2


def test_filter_diffs_no_match(sample_diffs):
    opts = FilterOptions(path_prefix="secret/other")
    result = filter_diffs(sample_diffs, opts)
    assert result == []


def test_filter_diffs_key_pattern(sample_diffs):
    opts = FilterOptions(key_pattern="*pass*")
    result = filter_diffs(sample_diffs, opts)
    assert len(result) == 1
    assert result[0].key == "password"
