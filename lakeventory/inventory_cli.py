"""Command-line interface for Lakeventory."""

import argparse
import copy
import logging
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from lakeventory.cache import InventoryCache
from lakeventory.client import build_workspace_client_with_config
from lakeventory.collectors import collect_all_findings, collect_findings_selective
from lakeventory.logging_config import configure_logging
from lakeventory.utils import set_progress_enabled
from lakeventory.output import (
    write_delta_excel,
    write_delta_markdown,
    write_excel,
    write_markdown,
)
from lakeventory.permissions_validator import PermissionsValidator
from lakeventory.workspace_backup import backup_workspace
from lakeventory.workspace_config import ConfigManager, WorkspaceConfig


logger = logging.getLogger(__name__)


def _visible_workspace_names(config) -> list:
    """Return workspace names excluding legacy 'default' alias when named envs exist."""
    names = list(config.workspaces.keys())
    if "default" in names and len(names) > 1:
        names = [name for name in names if name != "default"]
    return names


def _workspace_signature(workspace: WorkspaceConfig) -> tuple:
    """Build a signature to detect duplicated workspace configs."""
    host = (workspace.host or "").strip().lower().rstrip("/")
    auth_method = (workspace.auth_method or "").strip().lower()
    token = (workspace.token or "").strip()
    client_id = (workspace.client_id or "").strip()
    return (host, auth_method, token, client_id)


def _extract_workspace_id(host: str) -> str:
    if not host:
        return "workspace"
    parsed = urlparse(host)
    hostname = parsed.hostname or host
    match = re.search(r"adb-(\d+)", hostname)
    if match:
        return match.group(1)
    match = re.search(r"dbc-([a-z0-9-]+)", hostname)
    if match:
        return match.group(1)
    safe = re.sub(r"[^a-zA-Z0-9]+", "-", hostname).strip("-")
    return safe or "workspace"


def _apply_workspace_id(name: str, workspace_id: str) -> str:
    if "workspace_id" in name:
        return name.replace("workspace_id", workspace_id)
    path = Path(name)
    if path.stem in {"workspace_id", workspace_id}:
        return f"{workspace_id}{path.suffix}"
    return f"{workspace_id}_{path.stem}{path.suffix}"


def _infer_cloud_provider(host: str) -> str:
    value = (host or "").lower()
    if "azuredatabricks.net" in value:
        return "AZURE"
    if "cloud.databricks.com" in value or "databricks.com" in value:
        return "AWS"
    return ""



def _resolve_path(root: Path, path_str: str) -> Path:
    """Resolve relative paths from workspace root while preserving absolute paths."""
    path = Path(path_str)
    if path.is_absolute():
        return path.resolve()
    return (root / path).resolve()


def _apply_config_defaults(args, config) -> None:
    """Apply config.yaml defaults when CLI flags were omitted."""
    global_cfg = config.global_config

    if not args.collectors and getattr(global_cfg, "enabled_collectors", None):
        args.collectors = ",".join(global_cfg.enabled_collectors)

    if args.batch_size is None:
        args.batch_size = getattr(global_cfg, "batch_size", 200)
    if args.batch_sleep_ms is None:
        args.batch_sleep_ms = getattr(global_cfg, "batch_sleep_ms", 0)

    if args.include_runs is None:
        args.include_runs = getattr(global_cfg, "include_runs", False)
    if args.include_query_history is None:
        args.include_query_history = getattr(global_cfg, "include_query_history", False)
    if args.include_dbfs is None:
        args.include_dbfs = getattr(global_cfg, "include_dbfs", False)

    if not args.out and not args.out_xlsx:
        output_format = getattr(global_cfg, "output_format", "xlsx")
        if output_format == "markdown":
            args.out = "workspace_id.md"
        elif output_format == "all":
            args.out = "workspace_id.md"
            args.out_xlsx = "workspace_id.xlsx"
        else:
            args.out_xlsx = "workspace_id.xlsx"

    if not args.cache_dir:
        args.cache_dir = getattr(global_cfg, "cache_dir", ".inventory_cache")


def main() -> int:
    """Main entry point for inventory CLI."""
    parser = argparse.ArgumentParser(
        description="Inventory Databricks assets in a workspace.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  lakeventory                         # Run on default workspace
  lakeventory -w dev                  # Run on 'dev' workspace
  lakeventory --all-workspaces        # Run on all workspaces
  lakeventory --list-workspaces       # List configured workspaces
  lakeventory setup                   # Interactive setup wizard
        """
    )
    
    # Special commands
    parser.add_argument("command", nargs="?", help="Command: setup")
    
    # Multi-workspace support
    parser.add_argument("-w", "--workspace", help="Workspace name to use (from config.yaml)")
    parser.add_argument("--all-workspaces", action="store_true", help="Run on all configured workspaces")
    parser.add_argument("--list-workspaces", action="store_true", help="List configured workspaces and exit")
    
    parser.add_argument("--root", default=".", help="Workspace root to scan")
    parser.add_argument(
        "--out-dir",
        default="",
        help="Directory where output files will be written (empty = use global_config.output_dir from config.yaml)",
    )
    parser.add_argument("--out", default="", help="Output markdown file")
    parser.add_argument("--out-xlsx", default="", help="Output Excel file with categorized sheets")
    parser.add_argument(
        "--source",
        default="sdk",
        choices=["sdk"],
        help="Inventory source: sdk (databricks-sdk-py)",
    )
    parser.add_argument(
        "--collectors",
        default="",
        help="Comma-separated list of collectors to run (workspace,jobs,clusters,sql,mlflow,unity_catalog,repos,security,identities,serving,sharing,dbfs). If empty, runs all.",
    )
    parser.add_argument(
        "--serverless",
        action="store_true",
        help="Skip cluster-related collectors (clusters are managed by Databricks in serverless mode)",
    )
    parser.add_argument(
        "--include-runs",
        action="store_true",
        default=None,
        help="Include job runs (can be large)",
    )
    parser.add_argument(
        "--include-query-history",
        action="store_true",
        default=None,
        help="Include SQL query history (can be large)",
    )
    parser.add_argument(
        "--include-dbfs",
        action="store_true",
        default=None,
        help="Include DBFS root listing",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=None,
        help="Number of items per batch before sleeping",
    )
    parser.add_argument(
        "--batch-sleep-ms",
        type=int,
        default=None,
        help="Sleep time in ms between batches",
    )
    parser.add_argument(
        "--incremental",
        action="store_true",
        help="Only report changes since last run (requires --cache-dir)",
    )
    parser.add_argument(
        "--cache-dir",
        default="",
        help="Directory to store cache/snapshots (empty = use global_config.cache_dir from config.yaml)",
    )
    parser.add_argument(
        "--log-level",
        default="",
        choices=["error", "info", "verbose", "debug"],
        help="Logging verbosity level (CLI > INVENTORY_LOG_LEVEL > config.yaml > info)",
    )
    parser.add_argument(
        "--validate-permissions",
        action="store_true",
        help="Validate that user has required permissions before running inventory",
    )
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Skip permission validation (not recommended)",
    )
    parser.add_argument(
        "--backup-workspace",
        action="store_true",
        help="Backup workspace recursively using workspace export API and generate zip archive",
    )
    parser.add_argument(
        "--backup-out-dir",
        default="",
        help="Directory for workspace backup artifacts (CLI > config.yaml > out-dir)",
    )
    args = parser.parse_args()

    # Handle special commands first
    if args.command == "setup":
        from lakeventory.setup_wizard import run_setup_wizard
        return run_setup_wizard()
    
    # Load multi-workspace configuration
    config_manager = ConfigManager()
    config = config_manager.load()
    _apply_config_defaults(args, config)

    resolved_log_level = (
        args.log_level
        or getattr(config.global_config, "log_level", "info")
        or "info"
    )

    configure_logging(resolved_log_level)
    logger.debug("Parsed CLI args: %s", args)
    
    # Handle --list-workspaces
    if args.list_workspaces:
        names = _visible_workspace_names(config)
        if not names:
            print("No workspaces configured. Run 'lakeventory setup' to add workspaces.")
            return 0
        
        print(f"\n{'Name':<15} {'Host':<45} {'Auth Method':<20}")
        print('─' * 85)
        for name in names:
            ws = config.workspaces[name]
            default_marker = " *" if name == config.default_workspace else ""
            host_short = ws.host.replace('https://', '')[:43]
            print(f"{name:<15}{default_marker:<2} {host_short:<43} {ws.auth_method:<18}")
        
        if config.default_workspace:
            print(f"\n* = default workspace")
        return 0
    
    # Handle --all-workspaces
    if args.all_workspaces:
        workspace_names = _visible_workspace_names(config)
        if not workspace_names:
            logger.error("No workspaces configured. Run 'lakeventory setup' first.")
            return 1
        
        logger.info("Running inventory on all %d workspaces", len(workspace_names))

        seen_signatures = set()

        for workspace_name in workspace_names:
            workspace = config.get_workspace(workspace_name)
            if not workspace:
                logger.error("Workspace '%s' not found in configuration", workspace_name)
                continue

            signature = _workspace_signature(workspace)
            if signature in seen_signatures:
                logger.info(
                    "Skipping redundant workspace '%s' (same host/auth as a previous workspace)",
                    workspace_name,
                )
                continue
            seen_signatures.add(signature)

            logger.info("\n" + "=" * 60)
            logger.info("Processing workspace: %s", workspace_name)
            logger.info("=" * 60)

            workspace_args = copy.copy(args)
            workspace_args.out_dir = args.out_dir
            result = _run_single_workspace(workspace_args, config, workspace_name)
            if result != 0:
                logger.error("Failed to process workspace: %s", workspace_name)
        
        return 0
    
    # Handle single workspace (explicit or default)
    workspace_name = args.workspace or config.default_workspace
    
    if not workspace_name:
        logger.error("No workspace specified and no default configured.")
        logger.error("Run 'lakeventory setup' or use --workspace flag.")
        return 1
    
    return _run_single_workspace(args, config, workspace_name)


def _run_single_workspace(args, config, workspace_name: str = None) -> int:
    """Run inventory on a single workspace."""
    # Apply workspace configuration to environment if using config
    if workspace_name:
        workspace = config.get_workspace(workspace_name)
        if not workspace:
            logger.error("Workspace '%s' not found in configuration", workspace_name)
            return 1
        
        logger.info("Using workspace: %s (%s)", workspace_name, workspace.host)
        # In multi-workspace mode, always organize outputs by workspace directory.
        # Base directory priority: CLI --out-dir > workspace.output_dir > global output_dir.
        base_output_dir = args.out_dir or workspace.output_dir or config.global_config.output_dir
        workspace_output_dir = Path(base_output_dir) / workspace_name
        workspace_output_dir.mkdir(parents=True, exist_ok=True)
        args.out_dir = str(workspace_output_dir)

    root = Path(args.root).resolve()

    progress_enabled = getattr(config.global_config, "progress_enabled", True)
    set_progress_enabled(progress_enabled)
    timeout_seconds = getattr(config.global_config, "timeout", None)

    # Output directory: CLI > workspace.output_dir (already in args.out_dir) > global_config > default
    output_dir_str = args.out_dir or getattr(config.global_config, "output_dir", "output") or "output"
    out_dir = _resolve_path(root, output_dir_str)
    out_dir.mkdir(parents=True, exist_ok=True)
    logger.debug("Output directory: %s", out_dir)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")

    def with_timestamp(path: Path) -> Path:
        if path.suffix:
            return path.with_name(f"{path.stem}_{timestamp}{path.suffix}")
        return path.with_name(f"{path.name}_{timestamp}")

    # Build client and collect findings
    logger.info("Connecting to Databricks workspace...")
    workspace = config.get_workspace(workspace_name) if workspace_name else None
    client = build_workspace_client_with_config(
        root,
        host=getattr(workspace, "host", None),
        token=getattr(workspace, "token", None),
        client_id=getattr(workspace, "client_id", None),
        client_secret=getattr(workspace, "client_secret", None),
        timeout_seconds=timeout_seconds,
    )

    workspace_obj = config.get_workspace(workspace_name) if workspace_name else None
    workspace_host = getattr(workspace_obj, "host", "") if workspace_obj else ""
    workspace_id = _extract_workspace_id(workspace_host)
    cloud_provider = _infer_cloud_provider(workspace_host)
    logger.info("Using workspace_id: %s", workspace_id)

    backup_enabled = bool(args.backup_workspace) or bool(
        getattr(config.global_config, "backup_workspace", False)
    )

    if backup_enabled:
        backup_output_dir = args.backup_out_dir
        if not backup_output_dir:
            backup_output_dir = getattr(config.global_config, "backup_output_dir", "")
        if not backup_output_dir:
            backup_dir = out_dir
        else:
            backup_base_dir = _resolve_path(root, backup_output_dir)
            backup_dir = backup_base_dir / workspace_name if workspace_name else backup_base_dir
        backup_dir.mkdir(parents=True, exist_ok=True)

        logger.info("Running workspace backup mode...")
        backup_folder, backup_zip, backup_warnings = backup_workspace(client, workspace_id, backup_dir)
        print(f"Backup folder: {backup_folder}")
        print(f"Backup archive: {backup_zip}")
        if backup_warnings:
            print(f"Backup warnings: {len(backup_warnings)}")
            for warning in backup_warnings[:20]:
                print(f"  - {warning}")
            if len(backup_warnings) > 20:
                print(f"  ... and {len(backup_warnings) - 20} more")
        return 0

    if args.serverless:
        logger.info("Running in serverless mode (cluster collectors skipped)")

    # Validate permissions (always run unless explicitly skipped)
    if not args.skip_validation:
        logger.info("Validating user permissions...")
        validator = PermissionsValidator(client, cloud_provider=cloud_provider)
        all_passed, results, warnings_perms = validator.validate_all(exclude_heavy=not args.include_dbfs)
        print(validator.format_report())
        
        if not all_passed and args.validate_permissions:
            logger.error("Permission validation failed. Please check the report above.")
            return 1
        elif not all_passed:
            logger.warning("Some permissions are missing. Inventory may be incomplete. Use --validate-permissions to fail on errors.")
    else:
        logger.debug("Permission validation skipped (--skip-validation)")

    logger.info("Collecting inventory...")
    if args.serverless and not args.collectors:
        # In serverless mode, skip cluster-related collectors by default
        collectors_cfg = getattr(config.global_config, "serverless_collectors", None) or [
            "workspace", "jobs", "sql", "mlflow", "unity_catalog",
            "repos", "security", "identities", "serving", "sharing", "dbfs", "acl"
        ]
        collectors_list = ",".join(collectors_cfg)
        findings, warnings = collect_findings_selective(
            client,
            collectors=collectors_list,
            include_runs=args.include_runs,
            include_query_history=args.include_query_history,
            cloud_provider=cloud_provider,
            batch_size=args.batch_size,
            batch_sleep_ms=args.batch_sleep_ms,
        )
    elif args.collectors:
        findings, warnings = collect_findings_selective(
            client,
            collectors=args.collectors,
            include_runs=args.include_runs,
            include_query_history=args.include_query_history,
            cloud_provider=cloud_provider,
            batch_size=args.batch_size,
            batch_sleep_ms=args.batch_sleep_ms,
        )
    else:
        findings, warnings = collect_all_findings(
            client,
            include_runs=args.include_runs,
            include_query_history=args.include_query_history,
            include_dbfs=args.include_dbfs,
            cloud_provider=cloud_provider,
            batch_size=args.batch_size,
            batch_sleep_ms=args.batch_sleep_ms,
        )

    out_name = _apply_workspace_id(Path(args.out).name, workspace_id)
    out_path = out_dir / with_timestamp(Path(out_name))

    # Handle incremental mode
    if args.incremental:
        logger.info("Incremental mode: loading cache from %s", args.cache_dir)
        cache = InventoryCache(Path(args.cache_dir))
        previous = cache.get_latest_snapshot()
        delta_findings, stats = cache.compute_delta(findings, previous)
        
        logger.info(
            "Changes: +%s | -%s | ~%s | ✓%s",
            stats["added"],
            stats["removed"],
            stats["modified"],
            stats["unchanged"],
        )
        
        logger.info("Writing delta markdown report...")
        write_delta_markdown(delta_findings, stats, warnings, out_path)
        
        if args.out_xlsx:
            xlsx_name = _apply_workspace_id(Path(args.out_xlsx).name, workspace_id)
            xlsx_path = out_dir / with_timestamp(Path(xlsx_name))
            logger.info("Writing delta Excel report...")
            write_delta_excel(delta_findings, stats, warnings, xlsx_path)
        
        # Save current snapshot for next run
        cache.save_snapshot(findings)
        logger.info("Wrote delta report (%s changes) to %s", len(delta_findings), out_path)
    else:
        # Full mode (not incremental)
        logger.info("Writing markdown report...")
        write_markdown(findings, warnings, out_path)

        if args.out_xlsx:
            xlsx_name = _apply_workspace_id(Path(args.out_xlsx).name, workspace_id)
            xlsx_path = out_dir / with_timestamp(Path(xlsx_name))
            logger.info("Writing Excel report...")
            write_excel(findings, warnings, xlsx_path)

        logger.info("Wrote %s findings to %s", len(findings), out_path)
        
        # Save snapshot if cache enabled
        if args.cache_dir:
            cache = InventoryCache(Path(args.cache_dir))
            cache.save_snapshot(findings)
            logger.debug("Snapshot saved to %s", args.cache_dir)
    if warnings:
        logger.error("%s warnings captured (see output for details)", len(warnings))
        if logger.isEnabledFor(logging.DEBUG):
            for warning in warnings:
                logger.debug("warning: %s", warning)

    return 0

if __name__ == "__main__":
    sys.exit(main())