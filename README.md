# Databricks Inventory Script

This script connects to a Databricks workspace via `databricks-sdk-py` and generates an AS-IS inventory of assets.
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

## Configure Credentials
Use `.env` (or environment variables). You can start from `/.env-example`:
```
DATABRICKS_HOST=https://<workspace-host>
DATABRICKS_USERNAME=<admin-user>
DATABRICKS_PASSWORD=<admin-password>
# or
DATABRICKS_TOKEN=<pat>
```

## Run (Direct)
```bash
inventory_databricks_assets.py \
  --source sdk \
  --out databricks_as_is.md
```

## Run With Batching
```bash
inventory_databricks_assets.py \
  --source sdk \
  --out databricks_as_is.md \
  --batch-size 100 \
  --batch-sleep-ms 300
```

## Excel Output
```bash
inventory_databricks_assets.py \
  --source sdk \
  --out databricks_as_is.md \
  --out-xlsx databricks_as_is.xlsx
```

## Heavy Collectors (Optional)
```bash
/inventory_databricks_assets.py \
  --source sdk \
  --out databricks_as_is.md \
  --include-runs \
  --include-query-history \
  --include-dbfs
```

## Run With Makefile
```bash
make inventory
```

Full inventory (with heavy collectors):
```bash
make inventory-full INCLUDE_RUNS=1 INCLUDE_QUERY_HISTORY=1 INCLUDE_DBFS=1
```

## Output
The script writes a markdown report with:
- Summary counts by asset type
- Full listing of findings
- Warnings for endpoints that failed or are not permitted

## Troubleshooting
- Auth fails: verify `DATABRICKS_HOST` and either `DATABRICKS_USERNAME`/`DATABRICKS_PASSWORD` or `DATABRICKS_TOKEN`.
- Permissions: some endpoints require admin; check the `Warnings` section for denied APIs.
- Timeouts: reduce `--batch-size` and add `--batch-sleep-ms` (for example `--batch-size 50 --batch-sleep-ms 500`).
- Large workspaces: avoid heavy collectors unless needed (`--include-runs`, `--include-query-history`, `--include-dbfs`).
