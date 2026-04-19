"""Promote secrets from one namespace to another."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import hvac

from vaultpatch.config import NamespaceConfig


@dataclass
class PromoteResult:
    source: str
    target: str
    path: str
    success: bool
    error: Optional[str] = None


def _make_client(cfg: NamespaceConfig) -> hvac.Client:
    return hvac.Client(url=cfg.address, token=cfg.token, namespace=cfg.namespace)


def promote_path(
    source_cfg: NamespaceConfig,
    target_cfg: NamespaceConfig,
    path: str,
    dry_run: bool = False,
) -> PromoteResult:
    """Read secret at path from source and write it to target."""
    src_client = _make_client(source_cfg)
    mount = source_cfg.mount

    try:
        resp = src_client.secrets.kv.v2.read_secret_version(
            path=path, mount_point=mount
        )
        data: Dict[str, str] = resp["data"]["data"]
    except Exception as exc:  # noqa: BLE001
        return PromoteResult(
            source=source_cfg.name,
            target=target_cfg.name,
            path=path,
            success=False,
            error=f"read error: {exc}",
        )

    if dry_run:
        return PromoteResult(
            source=source_cfg.name,
            target=target_cfg.name,
            path=path,
            success=True,
        )

    tgt_client = _make_client(target_cfg)
    try:
        tgt_client.secrets.kv.v2.create_or_update_secret(
            path=path, secret=data, mount_point=target_cfg.mount
        )
    except Exception as exc:  # noqa: BLE001
        return PromoteResult(
            source=source_cfg.name,
            target=target_cfg.name,
            path=path,
            success=False,
            error=f"write error: {exc}",
        )

    return PromoteResult(
        source=source_cfg.name,
        target=target_cfg.name,
        path=path,
        success=True,
    )


def promote_paths(
    source_cfg: NamespaceConfig,
    target_cfg: NamespaceConfig,
    paths: List[str],
    dry_run: bool = False,
) -> List[PromoteResult]:
    return [
        promote_path(source_cfg, target_cfg, p, dry_run=dry_run) for p in paths
    ]
