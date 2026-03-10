# Lakeventory

Automated discovery and inventory of Databricks workspace assets and dependencies. Supports **multi-workspace management** with interactive setup wizard. Exports to Excel (default), Markdown, or JSON with cloud provider detection and workspace ID auto-sensing.

## Quick Start

### Single Workspace (Legacy)
```bash
# Install dependencies
pip install -r requirements.txt

# Run basic inventory (exports to Excel by default)
python -m lakeventory --source sdk

# Or with Markdown output
python -m lakeventory --source sdk --out report.md
```

### Multi-Workspace (Recommended)
```bash
# Interactive setup wizard
make setup
# or: python -m lakeventory setup

# List configured workspaces
make list-workspaces

# Run on specific workspace
make inventory-workspace WORKSPACE=prod

# Run on all workspaces
make inventory-all
```

**Via Makefile:**
```bash
make check       # Verify setup
make setup       # Interactive workspace configuration
make inventory   # Generate report (default workspace)
```

---

## What It Collects

- **Workspace**: Notebooks, files, directories
- **Compute**: Jobs, clusters, instance pools, policies, init scripts
- **SQL**: Warehouses, dashboards, queries, alerts, pipelines  
- **ML**: Experiments, registered models, model versions
- **Data**: Unity Catalog (catalogs, schemas, tables, volumes), External locations
- **Security**: Secret scopes, tokens, IP access lists, identities
- **Repos**: Git repositories and credentials
- **Sharing**: Delta Sharing assets (shares, recipients, providers)
- **Serving**: Serving endpoints, vector search, online tables
- **DBFS**: Root directory listing (optional)

---

## Documentation

| Topic | Link |
|-------|------|
| **Getting Started** | [Quick Start Guide](#quick-start) |
| **Multi-Workspace Setup** | [docs/MULTI_WORKSPACE.md](docs/MULTI_WORKSPACE.md) ✨ **NEW** |
| **Authentication** | [docs/AUTHENTICATION.md](docs/AUTHENTICATION.md) |
| **Permissions** | [docs/PERMISSIONS.md](docs/PERMISSIONS.md) |
| **Usage Examples** | [docs/USAGE.md](docs/USAGE.md) |
| **Troubleshooting** | [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) |

---

## Requirements

- Python 3.8+
- `databricks-sdk`, `openpyxl`, `tqdm`

```bash
pip install -r requirements.txt
```

---

## Configuration

### Option 1: Multi-Workspace (Recommended)

Use the interactive setup wizard to configure multiple workspaces:

```bash
make setup
```

Configuration is stored in `.lakeventory/config.yaml` with support for:
- Multiple workspaces (dev, staging, prod)
- PAT tokens or Service Principal authentication
- Workspace-specific output directories
- Global settings (format: xlsx, batch size, collectors)

**See [docs/MULTI_WORKSPACE.md](docs/MULTI_WORKSPACE.md)** for complete guide.

### Option 2: Single Workspace (Legacy)

Create `.env` file for single workspace:

```env
DATABRICKS_HOST=https://<workspace-host>
DATABRICKS_TOKEN=<your-pat-token>
OUTPUT_DIR=./output
```

**See [docs/AUTHENTICATION.md](docs/AUTHENTICATION.md)** for other auth methods (Service Principal).

---

## Verify Setup

```bash
make check
```

This validates:
- ✅ Python version (3.8+)
- ✅ Dependencies installed
- ✅ Credentials configured
- ✅ Workspace connection

---

## Common Commands

### Standard Run
```bash
python -m lakeventory --source sdk --out report.md
```

### With Excel Output
```bash
python -m lakeventory --source sdk --out-xlsx report.xlsx
```

### Validate Permissions First
```bash
python -m lakeventory --validate-permissions --source sdk
```

### Selective Collectors
```bash
python -m lakeventory --source sdk --collectors workspace,jobs,clusters
```

### Serverless Workspace
```bash
python -m lakeventory --source sdk --serverless
```

### Large Workspaces (with batching)
```bash
python -m lakeventory --source sdk \
  --batch-size 100 --batch-sleep-ms 300
```

**See [docs/USAGE.md](docs/USAGE.md)** for complete command reference and Makefile targets.

---

## Output

Reports include:
- Summary counts by asset type
- Full listing of workspace assets
- Warnings for API errors or permission issues
- Excel sheets (default) for easy browsing and filtering

### Single Workspace
Files are automatically timestamped and include workspace ID:
```
output/workspace_1234567_20260309_1549.xlsx
```

### Multi-Workspace
Organized by workspace name:
```
output/
├── prod/
│   ├── workspace_3456789_20260309_1549.xlsx
│   └── .inventory_cache/
├── staging/
│   └── workspace_2345678_20260309_1550.xlsx
└── dev/
    └── workspace_1234567_20260309_1551.xlsx
```

**Default format:** XLSX (Excel) — configurable per workspace or globally

---

## Troubleshooting

**See [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)** for:
- Authentication errors
- Permission issues
- Timeout handling
- Performance optimization
- Cloud-specific problems

---

## Project Structure

```
lakeventory/
├── __main__.py          # CLI entry point
├── inventory_cli.py     # Command-line interface
├── client.py            # Authentication
├── collectors.py        # 18+ asset collectors
├── output.py            # Markdown/Excel export
├── models.py            # Data structures
├── utils.py             # Utilities
├── config.py            # Constants
└── health_check.py      # Setup verification
```

---

## Testing

```bash
pip install -r requirements.txt
pytest -q
```

---

## Status

| Feature | Status |
|---------|--------|
| 40+ API endpoints | ✅ Complete |
| Multi-workspace support | ✅ Complete |
| Interactive setup wizard | ✅ Complete |
| Authentication (PAT, Service Principal) | ✅ Complete |
| Output (Excel, Markdown, JSON) | ✅ Complete |
| Cloud provider detection | ✅ Complete |
| Workspace ID auto-detect | ✅ Complete |
| Batching & timeouts | ✅ Complete |
| Selective collectors | ✅ Complete |
| Serverless mode | ✅ Complete |
| Permission validation | ✅ Complete |
| Testing (42 tests) | ✅ Complete |

---

## License

See LICENSE file for details.
