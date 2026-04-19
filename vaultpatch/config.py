"""Configuration loader for vaultpatch."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import yaml


@dataclass
class NamespaceConfig:
    name: str
    address: str
    token_env: str = "VAULT_TOKEN"
    mount: str = "secret"

    @property
    def token(self) -> Optional[str]:
        return os.environ.get(self.token_env)


@dataclass
class VaultPatchConfig:
    namespaces: List[NamespaceConfig] = field(default_factory=list)
    default_mount: str = "secret"

    @classmethod
    def from_file(cls, path: str | Path) -> "VaultPatchConfig":
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        with path.open() as f:
            raw = yaml.safe_load(f)

        if not isinstance(raw, dict):
            raise ValueError("Config file must be a YAML mapping")

        namespaces = [
            NamespaceConfig(
                name=ns["name"],
                address=ns["address"],
                token_env=ns.get("token_env", "VAULT_TOKEN"),
                mount=ns.get("mount", raw.get("default_mount", "secret")),
            )
            for ns in raw.get("namespaces", [])
        ]

        return cls(
            namespaces=namespaces,
            default_mount=raw.get("default_mount", "secret"),
        )

    def get_namespace(self, name: str) -> Optional[NamespaceConfig]:
        for ns in self.namespaces:
            if ns.name == name:
                return ns
        return None
