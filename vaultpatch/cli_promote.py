"""CLI sub-command: promote."""
import click

from vaultpatch.config import VaultPatchConfig
from vaultpatch.promote_hook import echo_promote_results, run_promote


@click.command("promote")
@click.option("--source", required=True, help="Source namespace name.")
@click.option("--target", required=True, help="Target namespace name.")
@click.option(
    "--path",
    "paths",
    multiple=True,
    required=True,
    help="Secret path(s) to promote (repeatable).",
)
@click.option("--dry-run", is_flag=True, default=False, help="Preview without writing.")
@click.pass_context
def promote_cmd(ctx: click.Context, source: str, target: str, paths: tuple, dry_run: bool) -> None:
    """Promote secrets from SOURCE namespace to TARGET namespace."""
    cfg: VaultPatchConfig = ctx.obj["config"]

    if source not in [n.name for n in cfg.namespaces]:
        raise click.BadParameter(f"Unknown namespace: {source}", param_hint="--source")
    if target not in [n.name for n in cfg.namespaces]:
        raise click.BadParameter(f"Unknown namespace: {target}", param_hint="--target")

    results = run_promote(cfg, source, target, list(paths), dry_run=dry_run)
    echo_promote_results(results, dry_run=dry_run)

    failed = [r for r in results if not r.success]
    if failed:
        ctx.exit(1)
