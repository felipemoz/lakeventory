# Lakeventory

[![Docker Publish](https://github.com/felipemoz/lakeventory/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/felipemoz/lakeventory/actions/workflows/docker-publish.yml)
[![Python Publish](https://github.com/felipemoz/lakeventory/actions/workflows/python-publish.yml/badge.svg)](https://github.com/felipemoz/lakeventory/actions/workflows/python-publish.yml)

Automated discovery and inventory of Databricks workspace assets and dependencies. Exports to Markdown or Excel with cloud provider detection and workspace ID auto-sensing.

## Installation

Método oficial (único documentado):

Instalação rápida (curl + bash):

```bash
curl -fsSL https://github.com/felipemoz/lakeventory/raw/main/scripts/install.sh | bash
```

Ou manualmente:

```bash
git clone https://github.com/felipemoz/lakeventory.git
cd lakeventory
make install
```

---

## Quick Start

```bash
make setup            # Cria/atualiza .lakeventory/config.yaml
make check            # Valida configuração e conexão
make inventory        # Executa inventário no workspace default
make inventory-all    # Executa em todos os workspaces do config.yaml
```

---

## Execution Model

O README documenta apenas execução via `make` para manter um fluxo único de operação.

Comandos operacionais:

```bash
make setup
make check
make inventory
make inventory-workspace WORKSPACE=prod
make inventory-all
make inventory-backup
```

Referência completa dos alvos: `make help`.

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
| **Workspace Backup** | [docs/BACKUP.md](docs/BACKUP.md) |
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
make install
```

---

## Configuration

Use o setup wizard para configurar workspaces:

```bash
make setup
```

Configuration is stored in `.lakeventory/config.yaml` with support for:
- Multiple workspaces (dev, staging, prod)
- PAT tokens or Service Principal authentication
- Workspace-specific output directories
- Global settings (format: xlsx, batch size, collectors)

**See [docs/MULTI_WORKSPACE.md](docs/MULTI_WORKSPACE.md)** for complete guide.

**See [docs/AUTHENTICATION.md](docs/AUTHENTICATION.md)** for auth methods (PAT, Service Principal).

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

### Setup e validação
```bash
make setup
make check
```

### Execução
```bash
make inventory
make inventory-workspace WORKSPACE=prod
make inventory-all
```

### Modos e variações
```bash
make inventory-validate
make inventory-selective COLLECTORS=workspace,jobs
make inventory-full
make inventory-incremental
make inventory-backup
make inventory-all-backup
```

**See [docs/USAGE.md](docs/USAGE.md)** for complete Makefile reference.

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

See LICENSE file for details.
