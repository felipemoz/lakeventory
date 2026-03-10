"""Enhanced CLI with subcommands for Lakeventory."""

import argparse
import logging
import sys
from pathlib import Path

from lakeventory import __version__
from lakeventory.cache import InventoryCache
from lakeventory.inventory_cli import main as legacy_main


logger = logging.getLogger(__name__)


def cmd_collect(args):
    """Run inventory collection (legacy compatibility)."""
    # Map new args to legacy format
    legacy_args = [
        "--source", args.source,
        "--out", args.out,
    ]
    
    if args.out_xlsx:
        legacy_args.extend(["--out-xlsx", args.out_xlsx])
    if args.incremental:
        legacy_args.append("--incremental")
    if args.include_runs:
        legacy_args.append("--include-runs")
    if args.include_query_history:
        legacy_args.append("--include-query-history")
    if args.include_dbfs:
        legacy_args.append("--include-dbfs")
    if args.validate_permissions:
        legacy_args.append("--validate-permissions")
    if args.timestamp:
        legacy_args.append("--timestamp")
    if args.cache_dir:
        legacy_args.extend(["--cache-dir", args.cache_dir])
    if args.output_dir:
        legacy_args.extend(["--output-dir", args.output_dir])
    if args.categories:
        legacy_args.extend(["--categories", ",".join(args.categories)])
    if args.batch_size:
        legacy_args.extend(["--batch-size", str(args.batch_size)])
    if args.batch_sleep_ms:
        legacy_args.extend(["--batch-sleep-ms", str(args.batch_sleep_ms)])
    
    # Call legacy main
    sys.argv = ["lakeventory"] + legacy_args
    return legacy_main()


def cmd_cache_list(args):
    """List cached snapshots."""
    cache = InventoryCache(Path(args.cache_dir))
    snapshots = cache.list_snapshots()
    
    if not snapshots:
        print(f"No snapshots found in {args.cache_dir}")
        return 0
    
    print(f"Cached snapshots in {args.cache_dir}:")
    print(f"{'Timestamp':<20} {'Findings':<10} {'Size':<10}")
    print("-" * 45)
    
    for snap in snapshots:
        timestamp = snap["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
        findings = snap.get("findings_count", "?")
        size = snap.get("size_bytes", 0)
        size_kb = f"{size / 1024:.1f} KB" if size > 0 else "?"
        print(f"{timestamp:<20} {findings:<10} {size_kb:<10}")
    
    print(f"\nTotal: {len(snapshots)} snapshot(s)")
    return 0


def cmd_cache_clear(args):
    """Clear cache directory."""
    cache_dir = Path(args.cache_dir)
    
    if not cache_dir.exists():
        print(f"Cache directory does not exist: {cache_dir}")
        return 0
    
    if args.force:
        confirm = "y"
    else:
        confirm = input(f"Clear all snapshots in {cache_dir}? [y/N]: ").lower()
    
    if confirm == "y":
        cache = InventoryCache(cache_dir)
        count = cache.clear_all()
        print(f"Cleared {count} snapshot(s) from {cache_dir}")
        return 0
    else:
        print("Cancelled")
        return 1


def cmd_diff(args):
    """Compare two inventory outputs."""
    from lakeventory.output import load_findings_from_file
    
    print(f"Comparing:\n  Baseline: {args.baseline}\n  Current:  {args.current}\n")
    
    baseline = load_findings_from_file(Path(args.baseline))
    current = load_findings_from_file(Path(args.current))
    
    # Simple diff logic
    baseline_keys = {f.get("name", f.get("id", str(i))): f for i, f in enumerate(baseline)}
    current_keys = {f.get("name", f.get("id", str(i))): f for i, f in enumerate(current)}
    
    added = set(current_keys.keys()) - set(baseline_keys.keys())
    removed = set(baseline_keys.keys()) - set(current_keys.keys())
    common = set(baseline_keys.keys()) & set(current_keys.keys())
    
    print(f"Summary:")
    print(f"  Added:    {len(added)}")
    print(f"  Removed:  {len(removed)}")
    print(f"  Unchanged: {len(common)}")
    print(f"  Total:    {len(current_keys)}")
    
    if args.verbose:
        if added:
            print(f"\nAdded ({len(added)}):")
            for key in sorted(added)[:10]:
                print(f"  + {key}")
            if len(added) > 10:
                print(f"  ... and {len(added) - 10} more")
        
        if removed:
            print(f"\nRemoved ({len(removed)}):")
            for key in sorted(removed)[:10]:
                print(f"  - {key}")
            if len(removed) > 10:
                print(f"  ... and {len(removed) - 10} more")
    
    return 0


def cmd_version(args):
    """Show version information."""
    print(f"Lakeventory version {__version__}")
    
    if args.verbose:
        import sys
        from databricks.sdk import __version__ as sdk_version
        
        print(f"Python: {sys.version.split()[0]}")
        print(f"Databricks SDK: {sdk_version}")
    
    return 0


def create_parser():
    """Create argument parser with subcommands."""
    parser = argparse.ArgumentParser(
        prog="lakeventory",
        description="Automated discovery and inventory of Databricks workspace assets",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output",
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # collect subcommand
    collect_parser = subparsers.add_parser(
        "collect",
        help="Run inventory collection",
        description="Collect inventory from Databricks workspace",
    )
    collect_parser.add_argument(
        "--source",
        default="sdk",
        choices=["sdk"],
        help="Collection source (default: sdk)",
    )
    collect_parser.add_argument(
        "--out",
        default="workspace_id.md",
        help="Output Markdown file path",
    )
    collect_parser.add_argument(
        "--out-xlsx",
        help="Output Excel file path",
    )
    collect_parser.add_argument(
        "--incremental",
        action="store_true",
        help="Run in incremental mode (only show changes)",
    )
    collect_parser.add_argument(
        "--include-runs",
        action="store_true",
        help="Include job run history",
    )
    collect_parser.add_argument(
        "--include-query-history",
        action="store_true",
        help="Include SQL query history",
    )
    collect_parser.add_argument(
        "--include-dbfs",
        action="store_true",
        help="Include DBFS root listing",
    )
    collect_parser.add_argument(
        "--validate-permissions",
        action="store_true",
        help="Validate service principal permissions",
    )
    collect_parser.add_argument(
        "--timestamp",
        action="store_true",
        help="Add timestamp to output filename",
    )
    collect_parser.add_argument(
        "--cache-dir",
        default=".cache/lakeventory",
        help="Cache directory path",
    )
    collect_parser.add_argument(
        "--output-dir",
        help="Output directory path",
    )
    collect_parser.add_argument(
        "--categories",
        nargs="+",
        help="Specific categories to collect",
    )
    collect_parser.add_argument(
        "--batch-size",
        type=int,
        help="Batch size for API calls",
    )
    collect_parser.add_argument(
        "--batch-sleep-ms",
        type=int,
        help="Sleep milliseconds between batches",
    )
    collect_parser.set_defaults(func=cmd_collect)
    
    # cache subcommand
    cache_parser = subparsers.add_parser(
        "cache",
        help="Manage cache snapshots",
        description="Manage inventory cache snapshots",
    )
    cache_subparsers = cache_parser.add_subparsers(dest="cache_command")
    
    # cache list
    cache_list_parser = cache_subparsers.add_parser(
        "list",
        help="List cached snapshots",
    )
    cache_list_parser.add_argument(
        "--cache-dir",
        default=".cache/lakeventory",
        help="Cache directory path",
    )
    cache_list_parser.set_defaults(func=cmd_cache_list)
    
    # cache clear
    cache_clear_parser = cache_subparsers.add_parser(
        "clear",
        help="Clear cache directory",
    )
    cache_clear_parser.add_argument(
        "--cache-dir",
        default=".cache/lakeventory",
        help="Cache directory path",
    )
    cache_clear_parser.add_argument(
        "-f", "--force",
        action="store_true",
        help="Force clear without confirmation",
    )
    cache_clear_parser.set_defaults(func=cmd_cache_clear)
    
    # diff subcommand
    diff_parser = subparsers.add_parser(
        "diff",
        help="Compare two inventory outputs",
        description="Compare baseline and current inventory",
    )
    diff_parser.add_argument(
        "--baseline",
        required=True,
        help="Baseline inventory file",
    )
    diff_parser.add_argument(
        "--current",
        required=True,
        help="Current inventory file",
    )
    diff_parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show detailed changes",
    )
    diff_parser.set_defaults(func=cmd_diff)
    
    # version subcommand
    version_parser = subparsers.add_parser(
        "version",
        help="Show version information",
    )
    version_parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show detailed version info",
    )
    version_parser.set_defaults(func=cmd_version)
    
    return parser


def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.debug else (logging.INFO if args.verbose else logging.WARNING)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    # If no command specified, show help
    if not args.command:
        parser.print_help()
        return 0
    
    # Execute command
    try:
        return args.func(args)
    except Exception as e:
        logger.error("Command failed: %s", e)
        if args.debug:
            raise
        return 1


if __name__ == "__main__":
    sys.exit(main())
