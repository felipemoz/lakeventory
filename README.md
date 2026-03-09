# Databricks Inventory Script

This script connects to a Databricks workspace via `databricks-sdk-py` and generates inventory of assets.
It is designed for large workspaces and supports batching to reduce timeouts.

## What It Collects
- Workspace objects (notebooks, files, directories)
- Jobs and optional job runs
- Clusters, instance pools, cluster policies, global init scripts, instance profiles
- SQL warehouses (including serverless flag)
- SQL dashboards, Lakeview (AI/BI) dashboards, queries, alerts
- MLflow experiments, registered models, model versions
- Unity Catalog: catalogs, schemas, tables, volumes
- External locations, storage credentials, connections, metastores
- Repos and git credentials
- Secret scopes, tokens, IP access lists
- Identities (users, groups, service principals)
- Serving endpoints, vector search, online tables
- Sharing (shares, recipients, providers)
- Optional DBFS root listing

## Requirements
- Python 3.x
- Dependencies: `databricks-sdk`, `openpyxl`

Install:
```bash
pip install -r requirements.txt
```

## ✅ Status

| Recurso | Status | Detalhes |
|---------|--------|----------|
| **Modularização** | ✅ Completo | 7 módulos + CLI entry point |
| **40+ API endpoints** | ✅ Completo | Workspace, Jobs, Clusters, SQL, MLflow, UC, etc. |
| **Cloud Provider Detection** | ✅ Completo | AWS/AZURE/GCP com API skipping |
| **Workspace ID Auto-detect** | ✅ Completo | Extrai de DATABRICKS_HOST |
| **Timestamps + Naming** | ✅ Completo | YYYYMMDD_HHMM format |
| **Selective Collectors** | ✅ Completo | `--collectors workspace,jobs,clusters` |
| **Serverless Mode** | ✅ Completo | `--serverless` flag que exclui cluster collectors |
| **Testing** | ✅ Completo | 5 test files com pytest |

## Project Structure
The script is organized into a modular package for maintainability:

```
inventory/
├── databricks_inventory/             # Modular package
│   ├── __init__.py                   # Package initialization
│   ├── __main__.py                   # CLI entry point (python -m databricks_inventory)
│   ├── inventory_cli.py              # CLI implementation
│   ├── config.py                     # Constants (SHEET_ORDER, KIND_TO_SHEET)
│   ├── models.py                     # Data structures (Finding dataclass)
│   ├── utils.py                      # Utilities (safe_iter, safe_list_call)
│   ├── client.py                     # Authentication (build_workspace_client)
│   ├── collectors.py                 # Asset collection functions (12 collectors)
│   └── output.py                     # Output formatting (markdown, Excel)
├── requirements.txt                  # Python dependencies
├── .env-example                      # Credentials template
├── Makefile                          # Automation targets
└── README.md                         # Documentation
```

This modular structure enables:
- **Easy testing**: Each module can be tested independently
- **Maintainability**: Changes to one component don't affect others
- **Reusability**: Collectors and utilities can be used in other scripts
- **Clarity**: Clear separation between configuration, business logic, and output

## Configure Credentials
Use `.env` (or environment variables). You can start from `.env-example`:
```
DATABRICKS_HOST=https://<workspace-host>

# Cloud Provider: AWS, AZURE, or GCP
# This helps skip APIs that are not available in specific clouds
DATABRICKS_CLOUD_PROVIDER=AZURE

DATABRICKS_USERNAME=<admin-user>
DATABRICKS_PASSWORD=<admin-password>
# or
DATABRICKS_TOKEN=<pat>
```

**Note:** Setting `DATABRICKS_CLOUD_PROVIDER` helps the script skip cloud-specific APIs:
- `AWS`: Enables Instance Profiles API
- `AZURE`: Skips Instance Profiles (Azure uses Managed Identities)
- `GCP`: Skips Instance Profiles (GCP uses Service Accounts)

## Run (Direct)
```bash
python -m databricks_inventory \
  --source sdk \
  --out report.md
```

## Run With Batching
```bash
python -m databricks_inventory \
  --source sdk \
  --out report.md \
  --batch-size 100 \
  --batch-sleep-ms 300
```

## Progress Bars
By default, collector iterations show progress bars in terminal output (via `tqdm`).

Disable progress bars when running in CI or non-interactive environments:
```bash
INVENTORY_PROGRESS=0 python -m databricks_inventory --source sdk --out report.md
```

## Logging Levels
You can control verbosity with `--log-level`:
- `error`: only errors
- `info` or `verbose`: standard run logs
- `debug`: detailed diagnostics (includes warning details)

Examples:
```bash
python -m databricks_inventory --source sdk --out report.md --log-level error
python -m databricks_inventory --source sdk --out report.md --log-level debug
```

## Excel Output
```bash
python -m databricks_inventory \
  --source sdk \
  --out-xlsx report.xlsx
```

## Output Folder, Workspace ID, and Timestamped Files
All outputs are written under an output directory (default: `output/`). Filenames automatically include the
`workspace_id` extracted from `DATABRICKS_HOST`, and are suffixed with the timestamp format `YYYYMMDD_HHMM`.
The script prints the detected `workspace_id` at startup.

Example:
```
output/<workspace_id>_report_20260309_1549.md
output/<workspace_id>_report_20260309_1549.xlsx
```

You can change the output directory:
```bash
python -m databricks_inventory \
  --source sdk \
  --out-dir reports \
  --out-xlsx report.xlsx
```

## Heavy Collectors (Optional)
```bash
python -m databricks_inventory \
  --source sdk \
  --include-runs \
  --include-query-history \
  --include-dbfs
```

## Selective Collectors (Run Only Specific Parts)
Use `--collectors` to run only specific collectors (one per Excel sheet):
```bash
python -m databricks_inventory \
  --source sdk \
  --collectors workspace,jobs,clusters
```

## Serverless Mode
If your Databricks workspace uses serverless compute, pass `--serverless` to skip cluster-related collectors:
```bash
python -m databricks_inventory \
  --source sdk \
  --serverless
```

In serverless mode, the following collectors are skipped by default:
- `clusters` — Not applicable (serverless compute) 
- Cluster policies, instance pools, global init scripts are skipped automatically

Available collectors:
- `workspace` — Notebooks, directories, files
- `jobs` — Jobs and optional runs (serverless-compatible)
- `clusters` — Clusters, policies, init scripts, instance pools (skipped in serverless)
- `sql` — Warehouses, dashboards, queries, alerts, pipelines (serverless SQL available)
- `mlflow` — Experiments, models, versions
- `unity_catalog` — Catalogs, schemas, tables, volumes
- `repos` — Git repositories, credentials
- `security` — Secret scopes, tokens, IP access lists
- `identities` — Users, groups, service principals
- `serving` — Serving endpoints, vector search, online tables
- `sharing` — Delta Sharing assets
- `dbfs` — DBFS root listing

## Run With Makefile
```bash
make inventory
```

Full inventory (with heavy collectors):
```bash
make inventory-full
```

Selective collectors:
```bash
make inventory-selective COLLECTORS=workspace,jobs,clusters
```

Serverless workspace:
```bash
make inventory SERVERLESS=1
make inventory-full SERVERLESS=1
```

Logging via Makefile:
```bash
make inventory LOG_LEVEL=debug
make inventory-debug
make inventory-error
make inventory-verbose
```

## Tests
Install dev dependencies and run pytest:
```bash
pip install -r requirements-dev.txt
pytest -q
```

## Output
The script writes a markdown report with:
- Summary counts by asset type
- Full listing of findings
- Warnings for endpoints that failed or are not permitted

When `--out-xlsx` is specified, an Excel file is generated with categorized sheets:
- **Notebooks**: All workspace notebooks (separate from other workspace objects)
- **Workspace Objects**: Directories and files
- **Jobs Runs**: Jobs and their execution history
- **Clusters Pools Policies**: Compute resources and configurations
- **SQL Warehouses**: SQL compute endpoints
- **SQL Dashboards Queries**: SQL analytics assets
- **MLflow**: Experiments, models, and versions
- **Unity Catalog**: Catalogs, schemas, tables, volumes
- **External Locations**: Storage credentials and connections
- **Repos Git**: Git repositories and credentials
- **Secrets Tokens IP**: Security assets
- **Identities**: Users, groups, service principals
- **Serving Vector Online**: Model serving and vector search
- **Sharing**: Delta Sharing assets
- **DBFS**: DBFS root content (when enabled)
- **Warnings**: API errors and unavailable endpoints

## Troubleshooting
- **Auth fails**: verify `DATABRICKS_HOST` and either `DATABRICKS_USERNAME`/`DATABRICKS_PASSWORD` or `DATABRICKS_TOKEN`.
- **Permissions**: some endpoints require admin; check the `Warnings` section for denied APIs.
- **Timeouts**: reduce `--batch-size` and add `--batch-sleep-ms` (for example `--batch-size 50 --batch-sleep-ms 500`).
- **Large workspaces**: avoid heavy collectors unless needed (`--include-runs`, `--include-query-history`, `--include-dbfs`).
- **Cloud-specific APIs**: Set `DATABRICKS_CLOUD_PROVIDER` (AWS/AZURE/GCP) to avoid errors from APIs not available in your cloud (e.g., Instance Profiles on Azure).
