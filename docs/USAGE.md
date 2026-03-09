# Usage Guide

## Quick Start

### Basic Run
```bash
python -m lakeventory --source sdk --out report.md
```

### With Excel Output
```bash
python -m lakeventory --source sdk --out-xlsx report.xlsx
```

### With Batching (for large workspaces)
```bash
python -m lakeventory \
  --source sdk \
  --out report.md \
  --batch-size 100 \
  --batch-sleep-ms 300
```

---

## Using Makefile

### Standard Run
```bash
make inventory
```

### Full Inventory (includes heavy collectors)
```bash
make inventory-full
```

### Selective Collectors
```bash
make inventory-selective COLLECTORS=workspace,jobs,clusters
```

### Serverless Mode
```bash
make inventory SERVERLESS=1
```

### Debug Logging
```bash
make inventory LOG_LEVEL=debug
```

### Validate Permissions
```bash
make inventory-validate
```

---

## Output Configuration

### Custom Output Directory

Via environment variable (`.env`):
```env
OUTPUT_DIR=./my-reports
```

Via CLI (highest priority):
```bash
python -m lakeventory \
  --source sdk \
  --out-dir reports \
  --out report.md
```

### Output Format

Files are automatically timestamped and include workspace ID:
```
output/<workspace_id>_report_20260309_1549.md
output/<workspace_id>_report_20260309_1549.xlsx
```

---

## Advanced Options

### Include Heavy Collectors
```bash
python -m lakeventory \
  --source sdk \
  --include-runs \
  --include-query-history \
  --include-dbfs
```

### Run Only Specific Collectors
```bash
python -m lakeventory \
  --source sdk \
  --collectors workspace,jobs,clusters,sql
```

Available collectors:
- `workspace` — Notebooks, directories, files
- `jobs` — Jobs and optional runs
- `clusters` — Clusters, policies, init scripts, instance pools
- `sql` — Warehouses, dashboards, queries, alerts, pipelines
- `mlflow` — Experiments, models, versions
- `unity_catalog` — Catalogs, schemas, tables, volumes
- `repos` — Git repositories, credentials
- `security` — Secret scopes, tokens, IP access lists
- `identities` — Users, groups, service principals
- `serving` — Serving endpoints, vector search, online tables
- `sharing` — Delta Sharing assets
- `dbfs` — DBFS root listing

### Serverless Workspace
```bash
python -m lakeventory \
  --source sdk \
  --serverless
```

This skips cluster-related collectors automatically.

---

## Logging & Progress

### Logging Levels
```bash
python -m lakeventory \
  --source sdk \
  --out report.md \
  --log-level debug  # error, info, verbose, debug
```

### Disable Progress Bars
```bash
INVENTORY_PROGRESS=0 python -m lakeventory --source sdk --out report.md
```

---

## Output Sheets (Excel)

When using `--out-xlsx`, the Excel file includes these sheets:

- **Notebooks**: Workspace notebooks
- **Workspace Objects**: Directories and files
- **Jobs Runs**: Jobs and execution history
- **Clusters Pools Policies**: Compute resources
- **SQL Warehouses**: SQL compute endpoints
- **SQL Dashboards Queries**: SQL analytics assets
- **MLflow**: Experiments, models, versions
- **Unity Catalog**: Catalogs, schemas, tables, volumes
- **External Locations**: Storage credentials and connections
- **Repos Git**: Git repositories and credentials
- **Secrets Tokens IP**: Security assets
- **Identities**: Users, groups, service principals
- **Serving Vector Online**: Model serving and vector search
- **Sharing**: Delta Sharing assets
- **DBFS**: DBFS root content (when enabled)
- **Warnings**: API errors and unavailable endpoints
