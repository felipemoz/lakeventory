"""Command-line interface for Lakeventory."""

import argparse
import logging
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from lakeventory.cache import InventoryCache
from lakeventory.client import build_workspace_client, load_output_dir
from lakeventory.collectors import collect_all_findings, collect_findings_selective
from lakeventory.logging_config import configure_logging
from lakeventory.output import (
    write_delta_excel,
    write_delta_markdown,
    write_excel,
    write_markdown,
)
from lakeventory.permissions_validator import PermissionsValidator
from lakeventory.workspace_config import ConfigManager, WorkspaceConfig


logger = logging.getLogger(__name__)


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
        help="Directory where output files will be written (empty = use OUTPUT_DIR from .env or default to ./output)",
    )
    parser.add_argument("--out", default="workspace_id.md", help="Output markdown file")
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
        help="Include job runs (can be large)",
    )
    parser.add_argument(
        "--include-query-history",
        action="store_true",
        help="Include SQL query history (can be large)",
    )
    parser.add_argument(
        "--include-dbfs",
        action="store_true",
        help="Include DBFS root listing",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=200,
        help="Number of items per batch before sleeping",
    )
    parser.add_argument(
        "--batch-sleep-ms",
        type=int,
        default=0,
        help="Sleep time in ms between batches",
    )
    parser.add_argument(
        "--incremental",
        action="store_true",
        help="Only report changes since last run (requires --cache-dir)",
    )
    parser.add_argument(
        "--cache-dir",
        default=".inventory_cache",
        help="Directory to store cache/snapshots (default: .inventory_cache)",
    )
    parser.add_argument(
        "--log-level",
        default=os.getenv("INVENTORY_LOG_LEVEL", "info"),
        choices=["error", "info", "verbose", "debug"],
        help="Logging verbosity level (error, info/verbose, debug)",
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
    args = parser.parse_args()

    # Handle special commands first
    if args.command == "setup":
        from lakeventory.setup_wizard import run_setup_wizard
        return run_setup_wizard()
    
    configure_logging(args.log_level)
    logger.debug("Parsed CLI args: %s", args)
    
    # Load multi-workspace configuration
    config_manager = ConfigManager()
    config = config_manager.load()
    
    # Handle --list-workspaces
    if args.list_workspaces:
        if not config.workspaces:
            print("No workspaces configured. Run 'lakeventory setup' to add workspaces.")
            return 0
        
        print(f"\n{'Name':<15} {'Host':<45} {'Auth Method':<20}")
        print('─' * 85)
        for name, ws in config.workspaces.items():
            default_marker = " *" if name == config.default_workspace else ""
            host_short = ws.host.replace('https://', '')[:43]
            print(f"{name:<15}{default_marker:<2} {host_short:<43} {ws.auth_method:<18}")
        
        if config.default_workspace:
            print(f"\n* = default workspace")
        return 0
    
    # Handle --all-workspaces
    if args.all_workspaces:
        if not config.workspaces:
            logger.error("No workspaces configured. Run 'lakeventory setup' first.")
            return 1
        
        logger.info("Running inventory on all %d workspaces", len(config.workspaces))
        
        for workspace_name in config.workspaces.keys():
            logger.info("\n" + "=" * 60)
            logger.info("Processing workspace: %s", workspace_name)
            logger.info("=" * 60)
            
            result = _run_single_workspace(args, config, workspace_name)
            if result != 0:
                logger.error("Failed to process workspace: %s", workspace_name)
        
        return 0
    
    # Handle single workspace (explicit or default)
    workspace_name = args.workspace or config.default_workspace
    
    if not workspace_name and not os.getenv("DATABRICKS_HOST"):
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
        config_manager = ConfigManager()
        config_manager.apply_workspace_env(workspace)
        
        # Override output directory with workspace-specific subdirectory
        # Use workspace-specific output_dir if configured, otherwise use global
        base_output_dir = workspace.output_dir or config.global_config.output_dir
        workspace_output_dir = Path(base_output_dir) / workspace_name
        workspace_output_dir.mkdir(parents=True, exist_ok=True)
        if not args.out_dir:
            args.out_dir = str(workspace_output_dir)

    root = Path(args.root).resolve()
    
    # Determine output directory: CLI arg > .env config > default
    if args.out_dir:
        output_dir_str = args.out_dir
    else:
        output_dir_str = load_output_dir(root)
    
    out_dir = (root / output_dir_str).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    logger.debug("Output directory: %s", out_dir)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")

    def with_timestamp(path: Path) -> Path:
        if path.suffix:
            return path.with_name(f"{path.stem}_{timestamp}{path.suffix}")
        return path.with_name(f"{path.name}_{timestamp}")

    workspace_id = _extract_workspace_id(os.getenv("DATABRICKS_HOST", ""))
    logger.info("Using workspace_id: %s", workspace_id)
    if args.serverless:
        logger.info("Running in serverless mode (cluster collectors skipped)")

    # Build client and collect findings
    logger.info("Connecting to Databricks workspace...")
    client = build_workspace_client(root)

    # Validate permissions (always run unless explicitly skipped)
    if not args.skip_validation:
        logger.info("Validating user permissions...")
        validator = PermissionsValidator(client)
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
        collectors_list = "workspace,jobs,sql,mlflow,unity_catalog,repos,security,identities,serving,sharing,dbfs"
        findings, warnings = collect_findings_selective(
            client,
            collectors=collectors_list,
            include_runs=args.include_runs,
            include_query_history=args.include_query_history,
            batch_size=args.batch_size,
            batch_sleep_ms=args.batch_sleep_ms,
        )
    elif args.collectors:
        findings, warnings = collect_findings_selective(
            client,
            collectors=args.collectors,
            include_runs=args.include_runs,
            include_query_history=args.include_query_history,
            batch_size=args.batch_size,
            batch_sleep_ms=args.batch_sleep_ms,
        )
    else:
        findings, warnings = collect_all_findings(
            client,
            include_runs=args.include_runs,
            include_query_history=args.include_query_history,
            include_dbfs=args.include_dbfs,
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