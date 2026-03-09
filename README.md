# Lakeventory

Automated discovery and inventory of Databricks workspace assets and dependencies. Exports to Markdown or Excel with cloud provider detection and workspace ID auto-sensing.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run basic inventory
python -m lakeventory --source sdk --out report.md

# Or with Excel output
python -m lakeventory --source sdk --out-xlsx report.xlsx
```

**Via Makefile:**
```bash
make check       # Verify setup
make inventory   # Generate report
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

### Create `.env` file

```env
DATABRICKS_HOST=https://<workspace-host>
DATABRICKS_TOKEN=<your-pat-token>
OUTPUT_DIR=./output
```

**See [docs/AUTHENTICATION.md](docs/AUTHENTICATION.md)** for other auth methods (Service Principal, Basic Auth).

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
- Excel sheets for easy browsing and filtering

Files are automatically timestamped and include workspace ID:
```
output/<workspace_id>_report_20260309_1549.md
```

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
| Authentication (SP, Token, Basic) | ✅ Complete |
| Output (Markdown, Excel) | ✅ Complete |
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
