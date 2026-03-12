# Lakeventory

[![Docker Publish](https://github.com/felipemoz/lakeventory/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/felipemoz/lakeventory/actions/workflows/docker-publish.yml)
[![Python Publish](https://github.com/felipemoz/lakeventory/actions/workflows/python-publish.yml/badge.svg)](https://github.com/felipemoz/lakeventory/actions/workflows/python-publish.yml)

Automated discovery and inventory of Databricks workspace assets and dependencies. Exports to Markdown or Excel with cloud provider detection and workspace ID auto-sensing.

## Installation

Official installation (curl + bash):

```bash
curl -fsSL https://github.com/felipemoz/lakeventory/raw/main/scripts/install.sh | bash
```

Manual alternative:

```bash
git clone https://github.com/felipemoz/lakeventory.git
cd lakeventory
make install
```

---

## Quick Start

```bash
make setup            # Creates/updates .lakeventory/config.yaml
make check            # Validates config and workspace connectivity
make inventory        # Runs inventory on default workspace
make inventory-all    # Runs inventory on all configured workspaces
```

---

## Execution Model

This README documents only the Makefile-based workflow to keep one operational path.

Core commands:

```bash
make setup
make check
make inventory
make inventory-workspace WORKSPACE=prod
make inventory-all
make inventory-backup
```

For all available targets, run:

```bash
make help
```

---

## What It Collects

- **Workspace**: notebooks, files, directories
- **Compute**: jobs, clusters, instance pools, policies, init scripts
- **SQL**: warehouses, dashboards, queries, alerts, pipelines
- **ML**: experiments, registered models, model versions
- **Data**: Unity Catalog (catalogs, schemas, tables, volumes), external locations
- **Security**: secret scopes, tokens, IP access lists, identities
- **Repos**: Git repositories and credentials
- **Sharing**: Delta Sharing assets (shares, recipients, providers)
- **Serving**: serving endpoints, vector search, online tables
- **DBFS**: root directory listing (optional)

---

## Documentation

| Topic | Link |
|-------|------|
| **Features Overview** | [docs/FEATURES.md](docs/FEATURES.md) |
| **Getting Started** | [Quick Start Guide](#quick-start) |
| **CLI Commands** | [docs/CLI.md](docs/CLI.md) |
| **Authentication** | [docs/AUTHENTICATION.md](docs/AUTHENTICATION.md) |
| **Multi-Workspace** | [docs/MULTI_WORKSPACE.md](docs/MULTI_WORKSPACE.md) |
| **Permissions** | [docs/PERMISSIONS.md](docs/PERMISSIONS.md) |
| **Workspace Backup** | [docs/BACKUP.md](docs/BACKUP.md) |
| **Incremental/Cache** | [docs/IMPLEMENTATION_CACHE.md](docs/IMPLEMENTATION_CACHE.md) |
| **Docker Deployment** | [docs/DOCKER.md](docs/DOCKER.md) |
| **Usage Examples** | [docs/USAGE.md](docs/USAGE.md) |
| **Troubleshooting** | [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) |

---

## CI/CD Status

The badges above reflect current pipeline status:
- Docker image build and publish (alpine, distroless, static)
- Python package build and publish (PyPI)

---

## Requirements

- Python 3.8+
- `databricks-sdk`, `openpyxl`, `tqdm`

```bash
make install
```

---

## Configuration

Use the setup wizard to configure workspaces:

```bash
make setup
```

Configuration is stored in `.lakeventory/config.yaml` with support for:
- Multiple workspaces (`dev`, `staging`, `prod`)
- PAT token or Service Principal authentication
- Workspace-specific output directories
- Global settings (`output_format`, `batch_size`, collectors, backup flags)

See:
- [docs/MULTI_WORKSPACE.md](docs/MULTI_WORKSPACE.md)
- [docs/AUTHENTICATION.md](docs/AUTHENTICATION.md)

---

## Verify Setup

```bash
make check
```

This validates:
- Python version (3.8+)
- Installed dependencies
- Configured credentials
- Workspace connectivity

---

## Common Commands

### Setup and validation

```bash
make setup
make check
```

### Execution

```bash
make inventory
make inventory-workspace WORKSPACE=prod
make inventory-all
```

### Modes and variants

```bash
make inventory-validate
make inventory-selective COLLECTORS=workspace,jobs
make inventory-full
make inventory-incremental
make inventory-backup
make inventory-all-backup
```

For complete Make target usage, see [docs/USAGE.md](docs/USAGE.md).

---

## Output

Reports include:
- Summary counts by asset type
- Full listing of workspace assets
- Warnings for API errors or permission issues
- Excel sheets (default) for easier filtering and navigation

### Single workspace

Files are timestamped automatically and include workspace ID.
Base directory comes from `output_dir` in `.lakeventory/config.yaml` (default `./output`):

```
<output_dir>/workspace_1234567_20260309_1549.xlsx
```

### Multi-workspace

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

Default format: `xlsx` (configurable globally or per workspace).

---

## Troubleshooting

See [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for:
- Authentication errors
- Permission issues
- Timeout handling
- Performance optimization
- Cloud-specific limitations

---

## Project Structure

```
lakeventory/
├── __main__.py          # CLI entry point
├── inventory_cli.py     # Main command-line workflow
├── client.py            # Databricks client/auth setup
├── collectors.py        # Asset collectors
├── output.py            # Markdown/Excel export
├── models.py            # Data structures
├── utils.py             # Utilities
├── config.py            # Constants
└── health_check.py      # Setup verification
```

---

## Documentation Language Standard

English is the standard language for this repository documentation.
All Markdown files should be written and maintained in English.

---


## Testing

```bash
make test
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
| Testing | ✅ Complete |

---

## License

See LICENSE for details.
