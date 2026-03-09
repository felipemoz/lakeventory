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

The tool supports **3 authentication methods** (in order of priority):

### 1️⃣ Service Principal (Recommended for Production/CI-CD)

Best for automation, CI/CD pipelines, and scheduled jobs.

**Create a Service Principal:**
1. Go to Databricks Admin Console → Identity & Access → Service Principals
2. Click "Add Service Principal" and create with name (e.g., "inventory-reader")
3. Assign required permissions (read-only access to workspace APIs)
4. Create a PAT (Personal Access Token) for the Service Principal

**Configure in `.env`:**
```env
DATABRICKS_HOST=https://<workspace-host>
DATABRICKS_CLIENT_ID=<service-principal-id>
DATABRICKS_CLIENT_SECRET=<service-principal-secret>
```

**Advantages:**
- ✅ Secure for production and CI/CD (no personal credentials)
- ✅ Easily rotatable (create new, deprecate old)
- ✅ Full auditability (logs show which SP did what)
- ✅ Can restrict permissions per SP

### 2️⃣ PAT Token (for Development/Testing)

Personal Access Token from your Databricks account.

**Create a PAT:**
1. In Databricks, click your profile → User Settings → Access tokens
2. Click "Generate new token" → Copy the token

**Configure in `.env`:**
```env
DATABRICKS_HOST=https://<workspace-host>
DATABRICKS_TOKEN=<your-pat-token>
```

**Advantages:**
- ✅ Easy to set up for development
- ✅ Tied to your user account
- ✅ Customizable expiration (7 days to 90 years)

### 3️⃣ Username + Password (Basic Auth)

Use your Databricks username and password.

**Configure in `.env`:**
```env
DATABRICKS_HOST=https://<workspace-host>
DATABRICKS_USERNAME=<your-username>
DATABRICKS_PASSWORD=<your-password>
```

⚠️ **Not recommended** for production or CI/CD. Use Service Principal instead.

### Priority & Automatic Detection

The tool **automatically detects** which authentication method is configured:

```
1. Service Principal (DATABRICKS_CLIENT_ID + DATABRICKS_CLIENT_SECRET) ← Highest Priority
2. PAT Token (DATABRICKS_TOKEN)
3. Basic Auth (DATABRICKS_USERNAME + DATABRICKS_PASSWORD) ← Lowest Priority
```

The first one found will be used. If multiple are configured, only the highest priority will be used.

## Health Check (Before Starting)

Before running inventory, verify that everything is properly configured:

```bash
make check
```

This performs 4 verification steps:

1. **Python Version**: Checks that Python 3.8+ is installed
2. **Dependencies**: Verifies `databricks-sdk`, `openpyxl`, and `tqdm` are installed
3. **Credentials**: Validates `DATABRICKS_HOST` and authentication (detects auth method automatically)
4. **Workspace Connection**: Connects to the workspace and verifies access

### Example Successful Check

```
======================================================================
INVENTORY TOOL HEALTH CHECK
======================================================================

[1/4] Python Version
  Python 3.9.6
  ✅ PASS (Python 3.8+)

[2/4] Dependencies
  ✅ databricks-sdk
  ✅ openpyxl
  ✅ tqdm

[3/4] Databricks Credentials
  ✅ DATABRICKS_HOST: https://dbc-abc123.cloud.databricks.com
  ✅ DATABRICKS_TOKEN: configured
  ✅ Cloud Provider: AZURE

[4/4] Workspace Connection
  Connecting to workspace...
  ✅ Connected to workspace ID: 1234567890
  ✅ Can list workspace objects

======================================================================
✅ ALL CHECKS PASSED - READY TO RUN INVENTORY
======================================================================

Next steps:
  1. Run: make inventory-validate
     (to validate API permissions)
  2. Run: make inventory
     (to generate workspace inventory)
```

If any check fails, the script will exit with an error message describing what needs to be fixed.

**Note:** Setting `DATABRICKS_CLOUD_PROVIDER` helps the script skip cloud-specific APIs:
- `AWS`: Enables Instance Profiles API
- `AZURE`: Skips Instance Profiles (Azure uses Managed Identities)
- `GCP`: Skips Instance Profiles (GCP uses Service Accounts)

## Service Principal Setup (Recommended for CI/CD)

### Create and Configure Service Principal

**Step 1: Create Service Principal in Databricks Admin Console**
```
1. Navigate to Admin Console → Identity & Access → Service Principals
2. Click "Add Service Principal"
3. Enter name: "inventory-reader" (or your preferred name)
4. Note the Client ID (e.g., a1b2c3d4-e5f6-7890-1234-567890abcdef)
```

**Step 2: Assign Permissions**
```
Option A - Create a Databricks group and assign to it:
1. Admin Console → Groups → Add Group "inventory-viewers"
2. Go to Service Principals → "inventory-reader" → Edit
3. Add to group "inventory-viewers"
4. Assign read permissions to the group

Option B - Use Terraform (recommended for production):
1. Define resource "databricks_service_principal" in code
2. Assign permissions via "databricks_permissions" or role binding
```

**Step 3: Create PAT Token for Service Principal**
```bash
# Via Databricks CLI
databricks pat create \
  --service-principal-id a1b2c3d4-e5f6-7890-1234-567890abcdef \
  --lifetime 365  # Token valid for 1 year
  --comment "inventory-reader token"
```
Output: `dapd1234567890abcdefghijklmnopqrst` (save this securely!)

**Step 4: Configure in Your CI/CD Pipeline**

For **GitHub Actions**:
```yaml
name: Run Databricks Inventory
on: [push]

jobs:
  inventory:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Inventory
        env:
          DATABRICKS_HOST: ${{ secrets.DATABRICKS_HOST }}
          DATABRICKS_CLIENT_ID: ${{ secrets.SP_CLIENT_ID }}
          DATABRICKS_CLIENT_SECRET: ${{ secrets.SP_CLIENT_SECRET }}
        run: python -m databricks_inventory --source sdk
```

For **Jenkins or GitLab CI**:
```bash
export DATABRICKS_HOST="https://your-workspace.cloud.databricks.com"
export DATABRICKS_CLIENT_ID="a1b2c3d4-e5f6-7890-1234-567890abcdef"
export DATABRICKS_CLIENT_SECRET="<secret-from-secure-storage>"
python -m databricks_inventory --source sdk
```

### Verify Service Principal Access

**Check which authentication method is detected:**
```bash
python -m databricks_inventory --log-level debug --root . 2>&1 | grep "authentication method"
# Output: INFO Detected authentication method: Service Principal (Client ID: a1b2c3d4...)
```

**Run health check with Service Principal:**
```bash
make check
# Will show: ✅ DATABRICKS_CLIENT_ID: configured
```

## Required Permissions

The user running this inventory script needs specific API permissions to access workspace assets.

### Minimum Required Permissions

The script requires **Admin panel access** or the following permissions:

| API Group | Required Permissions | Collectors Affected |
|-----------|----------------------|---------------------|
| **Workspace** | `workspace:read` (view notebooks, directories, files) | workspace |
| **Jobs** | `jobs:read` (list and view job details) | jobs |
| **Clusters** | `clusters:read` (list clusters and policies) | clusters |
| **SQL** | `sql:read` (view warehouses, dashboards, queries, alerts) | sql |
| **MLflow** | `experiments:read` (view experiments and models) | mlflow |
| **Unity Catalog** | `catalogs:read`, `schemas:read`, `tables:read`, `volumes:read`, `external_locations:read` | unity_catalog |
| **Repos** | `repos:read` (list repositories) | repos |
| **Secrets** | `secrets:read` (list secret scopes) | security |
| **Users/Identities** | `users:read`, `groups:read`, `service_principals:read` | identities |
| **Serving** | `serving_endpoints:read`, `vector_search_endpoints:read` | serving |
| **Sharing** | `shares:read` (Delta Sharing) | sharing |
| **DBFS** | `dbfs:read` (if `--include-dbfs` is used) | dbfs |

### Recommended Role

For a read-only inventory scan, create or request a role with these permissions:
```json
{
  "name": "inventory_reader",
  "permissions": [
    "workspace:read",
    "jobs:read",
    "clusters:read",
    "sql:read",
    "experiments:read",
    "catalogs:read",
    "schemas:read",
    "tables:read",
    "volumes:read",
    "external_locations:read",
    "repos:read",
    "secrets:read",
    "users:read",
    "groups:read",
    "service_principals:read",
    "serving_endpoints:read",
    "vector_search_endpoints:read",
    "shares:read"
  ]
}
```

### Checking Your Permissions

To verify what access the current user has, run with debug logging:
```bash
python -m databricks_inventory \
  --source sdk \
  --out report.md \
  --log-level debug
```

The debug output will show which endpoints succeed and which fail due to insufficient permissions. Failed endpoints will be listed in the `Warnings` sheet of the Excel report.

### API Endpoint Reference

Each collector accesses specific Databricks APIs:

- **workspace**: `workspace.list`, `workspace.export` (for notebook source code)
- **jobs**: `jobs.list`, `jobs.list_runs` (optional)
- **clusters**: `clusters.list`, `cluster_policies.list`, `global_init_scripts.list`, `instance_pools.list`, `instance_profiles.list`
- **sql**: `warehouses.list`, `dashboards.list`, `queries.list`, `alerts.list`, `pipelines.list`
- **mlflow**: `experiments.list`, `registered_models.list`, `model_versions.list`
- **unity_catalog**: `catalogs.list`, `schemas.list`, `tables.list`, `volumes.list`, `external_locations.list`, `storage_credentials.list`, `connections.list`, `metastores.list`
- **repos**: `repos.list`, `git_credentials.list`
- **security**: `secrets.list_scopes`, `tokens.list`, `ip_access_lists.list`
- **identities**: `users.list`, `groups.list`, `service_principals.list`
- **serving**: `serving_endpoints.list`, `vector_search_endpoints.list`, `online_tables.list`
- **sharing**: `shares.list`, `recipients.list`, `providers.list`
- **dbfs**: `dbfs.list` (optional, heavy collector)

### Notes on Cloud-Specific APIs

- **AWS**: Instance Profiles API requires additional AWS IAM permissions
- **Azure**: Instance Profiles are not available (uses Managed Identities instead)
- **GCP**: Instance Profiles are not available (uses Service Accounts instead)

When `DATABRICKS_CLOUD_PROVIDER` is set correctly, the script automatically skips cloud-specific non-applicable APIs.

## Validate Permissions (Before Running)

Before running the full inventory, you can validate that your user has the required permissions:

```bash
python -m databricks_inventory --validate-permissions --source sdk
```

This will:
- Connect to the Databricks workspace
- Test access to each API endpoint (workspace, jobs, clusters, SQL, MLflow, UC, etc.)
- Print a detailed permission validation report
- **Fail with exit code 1 if any permissions are missing**

### Example Permission Report

```
======================================================================
PERMISSION VALIDATION REPORT
======================================================================

✅ PASSED: 11/11 permission checks

Core APIs (Required):
  ✅ Workspace
  ✅ Jobs
  ✅ Clusters
  ✅ Sql
  ✅ Mlflow
  ✅ Unity Catalog
  ✅ Repos
  ✅ Security
  ✅ Identities
  ✅ Serving
  ✅ Sharing

======================================================================
```

### Example with Missing Permissions

```
======================================================================
PERMISSION VALIDATION REPORT
======================================================================

✅ PASSED: 9/11 permission checks

Core APIs (Required):
  ✅ Workspace
  ✅ Jobs
  ❌ Clusters
  ✅ Sql
  ✅ Mlflow
  ❌ Unity Catalog
  ✅ Repos
  ✅ Security
  ✅ Identities
  ✅ Serving
  ✅ Sharing

----------------------------------------------------------------------
PERMISSION ERRORS:

  ⚠️  clusters.list: 403 Forbidden - User does not have permission to access clusters
  ⚠️  catalogs.list: 403 Forbidden - User does not have permission to list UC catalogs

======================================================================
```

### Important Notes

- **Permission validation runs automatically by default** (unless `--skip-validation` is used)
- If permissions are missing, inventory will still run but may have incomplete results
- Use `--validate-permissions` to make it **fail on any permission errors** (recommended for CI/CD)
- Use `--skip-validation` to skip validation (not recommended)

Example with validation failure:
```bash
python -m databricks_inventory \
  --source sdk \
  --out report.md \
  --validate-permissions  # Will fail exit code 1 if permissions missing
```

### Makefile Targets for Validation

```bash
# Validate permissions and exit on error
make inventory-validate

# Run full inventory (with automatic permission validation)
make inventory

# Skip validation (not recommended)
make inventory SKIP_VALIDATION=1
```

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

### Output Directory (Alternative: Environment Variable)

Instead of using `--out-dir` every time, you can configure it in `.env`:
```
# .env
OUTPUT_DIR=./my-reports
```

The output directory is resolved in this order of priority:
1. **CLI argument** (`--out-dir`) - highest priority
2. **Environment variable** (`OUTPUT_DIR` in `.env` or OS env)
3. **Default** (`./output`) - fallback if neither above is set

Example:
```bash
# Uses OUTPUT_DIR from .env (or defaults to ./output)
make inventory

# Override via CLI (takes precedence over .env)
python -m databricks_inventory --out-dir /tmp/reports --source sdk
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
