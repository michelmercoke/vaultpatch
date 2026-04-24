"""Tests for vaultpatch.quota."""
from vaultpatch.diff import SecretDiff
from vaultpatch.quota import QuotaConfig, QuotaViolation, check_quota


def _diff(key: str, old: str | None, new: str | None) -> SecretDiff:
    return SecretDiff(path="secret/app", key=key, old_value=old, new_value=new)


def _diffs(n: int, path: str = "secret/app") -> list[SecretDiff]:
    return [SecretDiff(path=path, key=f"k{i}", old_value="x", new_value="y") for i in range(n)]


def test_no_violations_when_within_limits():
    cfg = QuotaConfig(max_changes=10, max_per_path=5)
    diffs_by_path = {"secret/app": _diffs(3)}
    result = check_quota(diffs_by_path, cfg)
    assert not result.exceeded
    assert result.violations == []


def test_total_changes_exceeded():
    cfg = QuotaConfig(max_changes=5, max_per_path=100)
    diffs_by_path = {
        "secret/a": _diffs(3, "secret/a"),
        "secret/b": _diffs(3, "secret/b"),
    }
    result = check_quota(diffs_by_path, cfg)
    assert result.exceeded
    paths = [v.path for v in result.violations]
    assert "(all paths)" in paths


def test_per_path_exceeded():
    cfg = QuotaConfig(max_changes=100, max_per_path=2)
    diffs_by_path = {"secret/app": _diffs(5)}
    result = check_quota(diffs_by_path, cfg)
    assert result.exceeded
    assert result.violations[0].path == "secret/app"
    assert result.violations[0].count == 5
    assert result.violations[0].limit == 2


def test_both_limits_exceeded():
    cfg = QuotaConfig(max_changes=3, max_per_path=2)
    diffs_by_path = {"secret/app": _diffs(4)}
    result = check_quota(diffs_by_path, cfg)
    assert result.exceeded
    assert len(result.violations) == 2


def test_empty_diffs_no_violations():
    cfg = QuotaConfig(max_changes=10, max_per_path=5)
    result = check_quota({}, cfg)
    assert not result.exceeded


def test_quota_config_from_dict():
    cfg = QuotaConfig.from_dict({"max_changes": 20, "max_per_path": 7})
    assert cfg.max_changes == 20
    assert cfg.max_per_path == 7


def test_quota_config_defaults():
    cfg = QuotaConfig.from_dict({})
    assert cfg.max_changes == 50
    assert cfg.max_per_path == 20


def test_violation_str():
    v = QuotaViolation(path="secret/x", reason="too many", count=10, limit=5)
    assert "secret/x" in str(v)
    assert "10" in str(v)
    assert "5" in str(v)
