"""Tests for vaultpatch/tag_hook.py CLI helper functions."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from vaultpatch.tag import save_tags, TagStore
from vaultpatch.tag_hook import cmd_tag_list, cmd_tag_remove, cmd_tag_set


@pytest.fixture()
def tag_file(tmp_path) -> str:
    return str(tmp_path / "tags.json")


def test_cmd_tag_set_creates_file(tag_file, capsys):
    cmd_tag_set("prod", "secret/db", ["critical"], tag_file)
    assert Path(tag_file).exists()
    out = capsys.readouterr().out
    assert "prod::secret/db" in out
    assert "critical" in out


def test_cmd_tag_set_overwrites_existing(tag_file, capsys):
    cmd_tag_set("prod", "secret/db", ["old"], tag_file)
    cmd_tag_set("prod", "secret/db", ["new"], tag_file)
    data = json.loads(Path(tag_file).read_text())
    tags = data["entries"][0]["tags"]
    assert tags == ["new"]


def test_cmd_tag_list_all(tag_file, capsys):
    cmd_tag_set("prod", "secret/db", ["critical"], tag_file)
    cmd_tag_set("prod", "secret/api", ["api"], tag_file)
    cmd_tag_list(None, tag_file)
    out = capsys.readouterr().out
    assert "secret/db" in out
    assert "secret/api" in out


def test_cmd_tag_list_filtered(tag_file, capsys):
    cmd_tag_set("prod", "secret/db", ["critical"], tag_file)
    cmd_tag_set("prod", "secret/api", ["api"], tag_file)
    cmd_tag_list("critical", tag_file)
    out = capsys.readouterr().out
    assert "secret/db" in out
    assert "secret/api" not in out


def test_cmd_tag_list_empty_store(tag_file, capsys):
    cmd_tag_list(None, tag_file)
    out = capsys.readouterr().out
    assert "(none)" in out


def test_cmd_tag_remove(tag_file, capsys):
    cmd_tag_set("prod", "secret/db", ["critical", "db"], tag_file)
    cmd_tag_remove("prod", "secret/db", "db", tag_file)
    data = json.loads(Path(tag_file).read_text())
    tags = data["entries"][0]["tags"]
    assert "db" not in tags
    assert "critical" in tags


def test_cmd_tag_remove_missing_path(tag_file, capsys):
    cmd_tag_remove("prod", "secret/missing", "db", tag_file)
    err = capsys.readouterr().err
    assert "No tags found" in err
