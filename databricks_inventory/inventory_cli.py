"""Command-line interface for Databricks inventory."""

import argparse
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from databricks_inventory.cache import InventoryCache
from databricks_inventory.client import build_workspace_client, load_output_dir
from databricks_inventory.collectors import collect_all_findings, collect_findings_selective
from databricks_inventory.logging_config import configure_logging
from databricks_inventory.output import (
    write_delta_excel,
    write_delta_markdown,
    write_excel,
    write_markdown,
)
from databricks_inventory.permissions_validator import PermissionsValidator


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
    parser = argparse.ArgumentParser(description="Inventory Databricks assets in a workspace.")
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

    configure_logging(args.log_level)
    logger.debug("Parsed CLI args: %s", args)

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
