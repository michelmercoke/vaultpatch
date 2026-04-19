"""Fetch secrets from Vault namespaces."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional

import hvac

from vaultpatch.config import NamespaceConfig


@dataclass
class FetchResult:
    namespace: str
    secrets: Dict[str, Dict[str, str]] = field(default_factory=dict)
    errors: Dict[str, str] = field(default_factory=dict)

    @property
    def success(self) -> bool:
        return len(self.errors) == 0


def _make_client(cfg: NamespaceConfig) -> hvac.Client:
    token = cfg.token()
    if not token:
        raise ValueError(f"No token available for namespace '{cfg.name}'")
    return hvac.Client(url=cfg.address, token=token, namespace=cfg.name)


def fetch_secrets(
    cfg: NamespaceConfig,
    paths: list[str],
    client: Optional[hvac.Client] = None,
) -> FetchResult:
    """Fetch secrets at given KV-v2 paths for a namespace."""
    result = FetchResult(namespace=cfg.name)
    try:
        c = client or _make_client(cfg)
    except ValueError as exc:
        for path in paths:
            result.errors[path] = str(exc)
        return result

    mount = cfg.mount
    for path in paths:
        try:
            resp = c.secrets.kv.v2.read_secret_version(
                path=path, mount_point=mount, raise_on_deleted_version=True
            )
            result.secrets[path] = resp["data"]["data"]
        except Exception as exc:  # noqa: BLE001
            result.errors[path] = str(exc)

    return result
