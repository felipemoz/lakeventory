# Lakeventory

[![Docker Publish](https://github.com/felipemoz/lakeventory/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/felipemoz/lakeventory/actions/workflows/docker-publish.yml)
[![Python Publish](https://github.com/felipemoz/lakeventory/actions/workflows/python-publish.yml/badge.svg)](https://github.com/felipemoz/lakeventory/actions/workflows/python-publish.yml)

Automated discovery and inventory of Databricks workspace assets and dependencies. Exports to Markdown or Excel with cloud provider detection and workspace ID auto-sensing.

## Installation

### Option 1: Install as CLI (Recommended)

```bash
# Clone repository
git clone https://github.com/felipemoz/lakeventory.git
cd lakeventory

# Install CLI
pip install -e .

# Use directly
lakeventory --version
lakeventory collect --out report.md
```

### Option 2: Use without Installation

### Single Workspace (Legacy)
```bash
# Install dependencies
pip install -r requirements.txt

# Run with Python module
python -m lakeventory --source sdk --out report.md
```

### Option 3: Standalone Executable

```bash
# Build executable (no Python required on target machine)
make build-exe

# Run
./dist/lakeventory version
./dist/lakeventory collect --out report.md
```

---

## Quick Start

```bash
# Using CLI (after pip install -e .)
lakeventory collect --out report.md

# Or with Excel output
lakeventory collect --out report.md --out-xlsx report.xlsx

# Legacy method (still works)
python -m lakeventory --source sdk --out report.md
```

**Via Makefile:**
```bash
make check       # Verify setup
make install-cli # Install CLI command
make inventory   # Generate report
```

---

## CLI Commands

The new CLI provides enhanced commands with better organization:

```bash
# Main commands
lakeventory collect         # Run inventory collection
lakeventory cache list      # List cached snapshots
lakeventory cache clear     # Clear cache
lakeventory diff            # Compare two inventories
lakeventory version         # Show version info

# Examples
lakeventory collect --incremental --out changes.md
lakeventory cache list
lakeventory diff --baseline old.md --current new.md --verbose
```

See [docs/CLI.md](docs/CLI.md) for complete CLI documentation.

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
| **CLI Commands** | [docs/CLI.md](docs/CLI.md) |
| **Authentication** | [docs/AUTHENTICATION.md](docs/AUTHENTICATION.md) |
| **Permissions** | [docs/PERMISSIONS.md](docs/PERMISSIONS.md) |
| **Usage Examples** | [docs/USAGE.md](docs/USAGE.md) |
| **Troubleshooting** | [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) |

---

## CI/CD Status

The badges above reflect the current pipeline status:
- Docker image build and publish (alpine, distroless, static)
- Python package build and publish (PyPI)

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
Files are timestamped automatically and include workspace ID.
The base directory comes from `output_dir` in `.lakeventory/config.yaml`
(default: `./output` if not overridden):
```
<output_dir>/workspace_1234567_20260309_1549.xlsx
```

### Multi-Workspace
Organized by workspace name, using `global_config.output_dir` or workspace-specific `output_dir`:
```
<output_dir>/
├── prod/
│   ├── workspace_3456789_20260309_1549.xlsx
│   └── .inventory_cache/
├── staging/
│   └── workspace_2345678_20260309_1550.xlsx
└── dev/
    └── workspace_1234567_20260309_1551.xlsx
```

**Default format:** XLSX (Excel) — configurable per workspace or globally
**Output directory:** configurable via YAML `output_dir` (global and/or per-workspace)

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
| Testing (89 tests) | ✅ Complete |

---

## License

See LICENSE file for details.
