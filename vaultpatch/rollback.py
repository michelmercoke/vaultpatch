"""Rollback support: revert secrets to a previous fetch snapshot."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

import hvac

from vaultpatch.config import NamespaceConfig
from vaultpatch.diff import SecretDiff, compute_diffs


@dataclass
class RollbackResult:
    namespace: str
    path: str
    success: bool
    error: Optional[str] = None
    reverted_keys: List[str] = field(default_factory=list)


def _make_client(ns: NamespaceConfig) -> hvac.Client:
    return hvac.Client(url=ns.address, token=ns.token, namespace=ns.namespace)


def rollback_path(
    ns: NamespaceConfig,
    path: str,
    snapshot: Dict[str, str],
) -> RollbackResult:
    """Write snapshot values back to Vault, reverting current state."""
    client = _make_client(ns)
    mount = ns.mount or "secret"
    try:
        current_resp = client.secrets.kv.v2.read_secret_version(
            path=path, mount_point=mount
        )
        current = current_resp["data"]["data"]
    except Exception as exc:
        return RollbackResult(namespace=ns.name, path=path, success=False, error=str(exc))

    diffs = compute_diffs(snapshot, current)
    if not diffs:
        return RollbackResult(namespace=ns.name, path=path, success=True, reverted_keys=[])

    try:
        client.secrets.kv.v2.create_or_update_secret(
            path=path, secret=snapshot, mount_point=mount
        )
    except Exception as exc:
        return RollbackResult(namespace=ns.name, path=path, success=False, error=str(exc))

    reverted = [d.key for d in diffs]
    return RollbackResult(namespace=ns.name, path=path, success=True, reverted_keys=reverted)
