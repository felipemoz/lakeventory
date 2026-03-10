# Usage Guide

## Multi-Workspace Support

### Setup Workspaces
```bash
# Interactive setup wizard
make setup
# or: python -m lakeventory setup
```

This wizard will guide you through:
1. Adding workspace configurations (host, auth method)
2. Testing connections
3. Setting default workspace
4. Configuring global settings

**See [MULTI_WORKSPACE.md](MULTI_WORKSPACE.md)** for complete guide.

### List Workspaces
```bash
make list-workspaces
# or: python -m lakeventory --list-workspaces
```

### Run on Specific Workspace
```bash
make inventory-workspace WORKSPACE=prod
# or: python -m lakeventory --workspace prod
```

### Run on All Workspaces
```bash
make inventory-all
# or: python -m lakeventory --all-workspaces
```

---

## Single Workspace (Legacy)

### Basic Run
```bash
python -m lakeventory --source sdk
```

### With Markdown Output (default is Excel/XLSX)
```bash
python -m lakeventory --source sdk --out report.md
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

### Multi-Workspace Commands
```bash
# Setup wizard
make setup

# List configured workspaces
make list-workspaces

# Run on default workspace
make inventory

# Run on specific workspace
make inventory-workspace WORKSPACE=prod

# Run on all workspaces
make inventory-all
```

### Single Workspace Commands
```bash
# Standard run
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

### Multi-Workspace Output

With multi-workspace configuration, each workspace gets its own directory:

```yaml
# .lakeventory/config.yaml
global_config:
  output_dir: ./output      # Base directory
  output_format: xlsx       # Default format (xlsx, markdown, json, all)

workspaces:
  prod:
    # Uses: ./output/prod/
  staging:
    output_dir: /mnt/reports  # Custom: /mnt/reports/staging/
```

Output structure:
```
output/
├── prod/
│   ├── workspace_3456789_20260309_1549.xlsx
│   └── .inventory_cache/
└── staging/
    └── workspace_2345678_20260309_1550.xlsx
```

### Custom Output Directory (Legacy)

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

**Default:** Excel (XLSX) format for easy browsing and filtering.

Files are automatically timestamped and include workspace ID:
```
output/workspace_1234567_20260309_1549.xlsx
output/workspace_1234567_20260309_1549.md  # if markdown format
```

**Change format:**
```yaml
# In .lakeventory/config.yaml
global_config:
  output_format: xlsx  # or: markdown, json, all
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
