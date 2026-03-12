"""CLI entry point for multi-workspace inventory."""

import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from lakeventory.logging_config import configure_logging
from lakeventory.multi_workspace import (
    load_workspaces_config,
    run_workspace_inventory,
    write_comparison_report,
)
from lakeventory.output import write_excel, write_markdown

logger = logging.getLogger(__name__)


def main() -> int:
    """Entry point for multi-workspace inventory CLI.

    Reads workspace definitions from a YAML config file, runs inventory for
    each workspace, writes individual reports, and produces a consolidated
    comparison Excel report.
    """
    parser = argparse.ArgumentParser(
        description="Run Lakeventory across multiple Databricks workspaces."
    )
    parser.add_argument(
        "--config",
        default="workspaces.yaml",
        help="Path to workspaces YAML configuration file (default: workspaces.yaml)",
    )
    parser.add_argument(
        "--out-dir",
        default="",
        help="Override output directory for all workspace reports",
    )
    parser.add_argument(
        "--comparison-out",
        default="",
        help="Override path for the consolidated comparison Excel report",
    )
    parser.add_argument(
        "--log-level",
        default="info",
        choices=["error", "info", "verbose", "debug"],
        help="Logging verbosity level (default: info)",
    )
    args = parser.parse_args()

    configure_logging(args.log_level)

    config_path = Path(args.config).resolve()
    base_dir = config_path.parent
    logger.info("Loading workspaces config from %s", config_path)

    try:
        config = load_workspaces_config(config_path)
    except FileNotFoundError as exc:
        logger.error("%s", exc)
        logger.error(
            "Create a workspaces.yaml from the example: cp workspaces.yaml.example workspaces.yaml"
        )
        return 1
    except (ValueError, RuntimeError) as exc:
        logger.error("Failed to parse workspaces config: %s", exc)
        return 1

    if not config.workspaces:
        logger.error("No workspaces defined in %s", config_path)
        return 1

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    workspace_results: Dict[str, List] = {}

    for ws_cfg in config.workspaces:
        logger.info("=== Processing workspace: %s ===", ws_cfg.name)
        try:
            workspace_id, findings, warnings = run_workspace_inventory(ws_cfg, base_dir)
        except Exception as exc:
            logger.error("Failed to inventory workspace '%s': %s", ws_cfg.name, exc)
            continue

        workspace_results[ws_cfg.name] = findings

        out_dir_str = args.out_dir or ws_cfg.output_dir
        out_dir = (base_dir / out_dir_str).resolve()
        out_dir.mkdir(parents=True, exist_ok=True)

        md_path = out_dir / f"{workspace_id}_report_{timestamp}.md"
        write_markdown(findings, warnings, md_path)
        logger.info("Wrote markdown report for '%s' to %s", ws_cfg.name, md_path)

        xlsx_path = out_dir / f"{workspace_id}_report_{timestamp}.xlsx"
        write_excel(findings, warnings, xlsx_path)
        logger.info("Wrote Excel report for '%s' to %s", ws_cfg.name, xlsx_path)

        if warnings:
            logger.warning(
                "%s warnings captured for workspace '%s'", len(warnings), ws_cfg.name
            )

    if not workspace_results:
        logger.error("No workspace inventories succeeded.")
        return 1

    comp_dir_str = args.out_dir or config.comparison.output_dir
    comp_dir = (base_dir / comp_dir_str).resolve()
    comp_dir.mkdir(parents=True, exist_ok=True)

    if args.comparison_out:
        comp_xlsx_path = Path(args.comparison_out).resolve()
    else:
        comp_name = config.comparison.out_xlsx
        stem = Path(comp_name).stem
        suffix = Path(comp_name).suffix
        comp_xlsx_path = comp_dir / f"{stem}_{timestamp}{suffix}"

    write_comparison_report(workspace_results, comp_xlsx_path)
    logger.info(
        "Wrote comparison report (%d workspaces) to %s",
        len(workspace_results),
        comp_xlsx_path,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
