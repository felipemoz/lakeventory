# Workspace Backup

Databricks workspace backup guide using `.dbc` exports with final `.zip` packaging.

## Overview

Backup mode recursively exports workspace objects and generates:

- A folder containing exported `.dbc` files
- A consolidated `.zip` archive

Flow:
1. List directories/objects recursively
2. Export each item using the Workspace Export API
3. Save locally as `.dbc`
4. Generate final `.zip`

## Configuration via `config.yaml`

File: `.lakeventory/config.yaml`

```yaml
global_config:
  output_dir: ./output
  backup_workspace: true
  backup_output_dir: ./backups
```

- `backup_workspace`: enables backup before inventory collection
- `backup_output_dir`: backup base directory
  - empty (`""`) => uses `output_dir`

## Configuration via Environment Variables (CI/CD)

Use temporary overrides in pipelines:

```bash
export BACKUP_WORKSPACE=true
export BACKUP_OUTPUT_DIR=./backups
```

## Parameter Precedence

Order of precedence:

1. CLI flags
2. `config.yaml`
3. Environment variables (`BACKUP_WORKSPACE`, `BACKUP_OUTPUT_DIR`)

## Commands

### Single Workspace Backup

```bash
python -m lakeventory --workspace prod --backup-workspace
```

With Makefile:

```bash
make inventory-backup BACKUP_OUT_DIR=./backups
```

### Backup All Workspaces

```bash
python -m lakeventory --all-workspaces --backup-workspace
```

With Makefile:

```bash
make inventory-all-backup BACKUP_OUT_DIR=./backups
```

## Setup Wizard (`make setup`)

The wizard includes:

- `Configure backup settings`

It writes `backup_workspace` and `backup_output_dir` in `global_config`.

## Output Structure

Example:

```text
<backup_output_dir>/
└── workspace_backup_<workspace_id>_<timestamp>/
    ├── Users/admin@example.com/Notebook.dbc
    └── Shared/Project/file.txt.dbc

<backup_output_dir>/workspace_backup_<workspace_id>_<timestamp>.zip
```

## Size Limitation (10 MB)

Some API paths have per-request/content limits. To reduce failures, backup exports items one by one instead of attempting a single full-workspace export.

If an item exceeds limits or cannot be exported, it is listed under `Backup warnings`.
