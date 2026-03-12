# Lakeventory Features & Functionality

Complete reference for all Lakeventory capabilities for discovering and inventorying Databricks workspace assets.

## Core Features

### 1. Multi-Workspace Management ✅
- **Setup Wizard**: Interactive configuration of multiple workspaces
- **Workspace-Specific Config**: Store configuration per workspace in `.lakeventory/config.yaml`
- **Custom Output Directories**: Override output location per workspace
- **Batch Operations**: Run inventory on all workspaces with single command
- **Service Principal & PAT Auth**: Support for both authentication methods per workspace

**Commands:**
```bash
make setup                                    # Interactive setup wizard
make list-workspaces                         # List all configured workspaces
make inventory-workspace WORKSPACE=prod      # Run on specific workspace
make inventory-all                           # Run on all workspaces
```

**Documentation:** [MULTI_WORKSPACE.md](MULTI_WORKSPACE.md)

---

### 2. Comprehensive Asset Discovery ✅

Collects inventory from 12 asset categories:

| Category | Assets Collected |
|----------|-----------------|
| **Workspace** | Notebooks, directories, files |
| **Compute** | Jobs, clusters, instance pools, policies, init scripts |
| **SQL** | Warehouses, dashboards, queries, alerts, pipelines |
| **ML** | Experiments, registered models, model versions |
| **Data** | Unity Catalog (catalogs, schemas, tables, volumes), external locations |
| **Security** | Secret scopes, tokens, IP access lists |
| **Repos** | Git repositories, credentials |
| **Identities** | Users, groups, service principals |
| **Serving** | Serving endpoints, vector search, online tables |
| **Sharing** | Delta Sharing assets (shares, recipients, providers) |
| **DBFS** | Root directory listing (optional) |
| **Special** | Cloud provider detection, workspace ID auto-sensing |

**Selective Collection:**
```bash
make inventory-selective COLLECTORS=workspace,jobs,clusters
```

**Documentation:** [USAGE.md](USAGE.md) - "Output Sheets (Excel)"

---

### 3. Incremental Updates & Change Tracking ✅
- **Full Snapshots**: First run captures complete workspace state
- **Delta Mode**: Subsequent runs report only changes (added/removed/modified)
- **Snapshot Management**: List, clear, and manage cached snapshots
- **10x Speed Improvement**: Incremental runs complete in <2 minutes vs 5-10 for full

**Commands:**
```bash
make inventory                               # Full inventory (creates cache)
make inventory-incremental                   # Delta mode (shows only changes)
make cache-clear                             # Clear all snapshots
make cache-info                              # View cache status
```

**Documentation:** [IMPLEMENTATION_CACHE.md](IMPLEMENTATION_CACHE.md)

---

### 4. Workspace Backup ✅
- **Export All Objects**: Recursively exports all workspace items as `.dbc` files
- **ZIP Archive**: Generates consolidated backup file
- **Size Limitations**: Handles API limits by exporting items individually
- **Multi-Workspace Backup**: Backup all workspaces in one command

**Commands:**
```bash
make inventory-backup                        # Backup single workspace
make inventory-all-backup BACKUP_OUT_DIR=./backups  # Backup all workspaces
python -m lakeventory --backup-workspace --workspace prod
```

**Documentation:** [BACKUP.md](BACKUP.md)

---

### 5. Multiple Output Formats ✅

| Format | Best For | Features |
|--------|----------|----------|
| **Excel (XLSX)** | Default, spreadsheets | Categorized sheets, filtering, sorting, formatting |
| **Markdown (MD)** | Documentation, git, reports | Plain text, version control friendly |
| **JSON** | APIs, programmatic use | Machine-readable, structured data |
| **All** | Archive | Generates all three formats simultaneously |

**Commands:**
```bash
python -m lakeventory --source sdk --out report.md                    # Markdown
python -m lakeventory --source sdk --out-xlsx report.xlsx            # Excel
python -m lakeventory --source sdk --out report.md --out-xlsx report.xlsx  # Both
```

**Configuration:**
```yaml
# .lakeventory/config.yaml
global_config:
  output_format: xlsx  # or: markdown, json, all
```

**Documentation:** [USAGE.md](USAGE.md) - "Output Format"

---

### 6. Permission Validation ✅
- **Pre-Flight Checks**: Validate permissions before running inventory
- **Detailed Reports**: Shows which APIs require which permissions
- **Fail on Missing**: Exits with error code if permissions insufficient
- **Health Checks**: Verify workspace connectivity and credentials

**Commands:**
```bash
make check                                   # Full health check
python -m lakeventory --validate-permissions --source sdk
```

**Documentation:** [PERMISSIONS.md](PERMISSIONS.md)

---

### 7. Authentication Methods ✅

#### Service Principal (Recommended for Production)
- OAuth 2.0 authentication
- No personal credentials
- Full audit trail
- Perfect for CI/CD pipelines
- Easily rotatable

**Configuration:**
```yaml
auth_method: service_principal
client_id: xxxx-xxxx-xxxx
client_secret: yyyy
tenant_id: zzzz-zzzz-zzzz
```

#### PAT Token (For Development)
- Personal Access Token
- Tied to user account
- Customizable expiration (7 days to 90 years)
- Easy to set up

**Configuration:**
```yaml
auth_method: pat
token: dapi...
```

**Documentation:** [AUTHENTICATION.md](AUTHENTICATION.md)

---

### 8. Performance Optimization ✅

#### Batching for Large Workspaces
- **Configurable Batch Size**: Control items per batch before sleeping
- **Configurable Sleep Time**: Add delays to reduce API pressure
- **Reduces Timeouts**: Prevents "Request timed out" errors on large workspaces

**Commands:**
```bash
python -m lakeventory \
  --source sdk \
  --batch-size 100 \
  --batch-sleep-ms 300
```

#### Serverless Mode
- Automatically skips cluster-related collectors
- Optimized for serverless Databricks workspaces

**Command:**
```bash
make inventory SERVERLESS=1
# or
python -m lakeventory --serverless
```

#### Selective Collectors
- Run only needed collectors to reduce execution time
- Skip heavy operations (job runs, query history)

**Commands:**
```bash
make inventory-selective COLLECTORS=workspace,jobs,clusters
python -m lakeventory --collectors workspace,jobs,sql  # Skip expensive collectors
```

**Documentation:** [USAGE.md](USAGE.md) - "Advanced Options"

---

### 9. Logging & Debugging ✅

| Level | Use Case |
|-------|----------|
| **error** | Only failures (production) |
| **info** | Basic status (default) |
| **verbose** | Detailed progress |
| **debug** | Full diagnostic information (troubleshooting) |

**Commands:**
```bash
python -m lakeventory --log-level debug --out report.md 2>&1 | tee debug.log
INVENTORY_PROGRESS=0 python -m lakeventory --source sdk  # Disable progress bars
```

**Documentation:** [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - "Debug Mode"

---

### 10. CI/CD Integration ✅
- **Environment Variables**: Supports DATABRICKS_* env vars for credentials
- **GitHub Actions**: Example workflows included
- **Jenkins/GitLab CI**: Compatible with standard CI/CD patterns
- **Docker Support**: Three Dockerfile variants for different use cases
- **Docker Compose**: Scheduled runs with persistent volumes

**Dockerfile Variants:**
```bash
docker build -t lakeventory:alpine .              # Standard (202 MB)
docker build -f Dockerfile.distroless -t lakeventory:distroless .  # Ultra-minimal (157 MB)
docker build -f Dockerfile.static -t lakeventory:static .         # Portable (91.6 MB)
```

**Documentation:** [DOCKER.md](DOCKER.md) | [AUTHENTICATION.md](AUTHENTICATION.md) - "Setup for CI/CD"

---

### 11. Cloud Provider Support ✅
- **AWS**: Full support including instance profiles
- **Azure**: Support with managed identities
- **GCP**: Support with service accounts
- **Auto-Detection**: Detects cloud provider from workspace URL
- **Cloud-Specific Collectors**: Skips unavailable APIs per cloud

**Environment Variable:**
```bash
DATABRICKS_CLOUD_PROVIDER=AZURE  # or AWS, GCP
```

**Documentation:** [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - "Cloud-Specific Issues"

---

### 12. Delta Sharing Support ✅
- **Share Discovery**: Lists all Delta Sharing assets
- **Recipients & Providers**: Captures sharing configuration
- **Share Details**: Documents shared objects and permissions

**Included in:** Default inventory (no special flags needed)

---

## Installation & Distribution

### Installation Methods ✅
1. **From Source (Editable)**
```bash
git clone https://github.com/felipemoz/lakeventory.git
cd lakeventory
pip install -e .
```

2. **From PyPI (Future)**
```bash
pip install lakeventory
```

3. **Standalone Executable**
```bash
bash scripts/build_executable.sh
./dist/lakeventory collect --out report.md
```

**Documentation:** [CLI.md](CLI.md) - "Installation Methods"

---

## Makefile Convenience Targets ✅

| Target | Purpose |
|--------|---------|
| `make setup` | Interactive setup wizard |
| `make check` | Health check and validation |
| `make install` | Install dependencies |
| `make inventory` | Run on default workspace |
| `make inventory-workspace` | Run on specific workspace |
| `make inventory-all` | Run on all workspaces |
| `make inventory-incremental` | Delta mode report |
| `make inventory-backup` | Backup workspace |
| `make cache-clear` | Clear snapshots |
| `make test` | Run test suite |
| `make docker-build` | Build Docker image |
| `make docker-build-all` | Build all Docker variants |

**Documentation:** See output of `make help`

---

## Advanced Configuration

### Configuration File (`.lakeventory/config.yaml`)
```yaml
version: "1.0"
default_workspace: prod

workspaces:
  prod:
    host: https://adb-xxx.azuredatabricks.net
    auth_method: service_principal
    client_id: xxxx-xxxx-xxxx
    client_secret: yyyy
    tenant_id: zzzz-zzzz-zzzz
    output_dir: ./reports/prod  # Optional override

global_config:
  output_dir: ./output
  output_format: xlsx
  batch_size: 200
  batch_sleep_ms: 50
  include_runs: false
  include_query_history: false
  include_dbfs: false
  enabled_collectors:
    - workspace
    - jobs
    - clusters
    - sql
    - mlflow
    - unity_catalog
    - repos
    - security
    - identities
    - serving
```

**Documentation:** [MULTI_WORKSPACE.md](MULTI_WORKSPACE.md) - "Configuration File"

---

## What's Included

### Documentation (10 files)
- ✅ README.md - Quick start and overview
- ✅ CLI.md - Installation and CLI reference
- ✅ AUTHENTICATION.md - Auth methods (Service Principal, PAT, CI/CD)
- ✅ PERMISSIONS.md - Required permissions and validation
- ✅ USAGE.md - Usage examples and command reference
- ✅ MULTI_WORKSPACE.md - Multi-workspace configuration
- ✅ BACKUP.md - Workspace backup guide
- ✅ DOCKER.md - Docker build and run guide
- ✅ TROUBLESHOOTING.md - Common issues and solutions
- ✅ IMPLEMENTATION_CACHE.md - Cache and incremental updates
- ✅ FEATURES.md - This file

### Docker Support
- ✅ Dockerfile (Alpine, 202 MB)
- ✅ Dockerfile.distroless (Ultra-minimal, 157 MB)
- ✅ Dockerfile.static (PyInstaller portable, 91.6 MB)
- ✅ docker-compose.yml

### Tests & Quality
- ✅ Comprehensive test suite
- ✅ CI/CD pipelines (GitHub Actions)
- ✅ Health checks and validation
- ✅ Permission validators

### Examples & Templates
- ✅ Configuration template (workspaces.yaml.example)
- ✅ CI/CD examples (GitHub Actions, Jenkins, GitLab)
- ✅ Makefile with 30+ convenience targets
- ✅ Contributors guide

---

## Quick Reference by Use Case

### Use Case: Audit Compliance Report
```bash
make setup                              # Configure workspace
make check                              # Validate permissions
make inventory                          # Run full inventory
# Output: Excel file with all assets
```

### Use Case: Track Changes Daily
```bash
# Day 1: Create baseline
make inventory

# Day 2+: See only changes
make inventory-incremental
# Output: Only added/removed/modified items
```

### Use Case: CI/CD Pipeline
```bash
# GitHub Actions: Set secrets for DATABRICKS_HOST, DATABRICKS_CLIENT_ID, etc.
export DATABRICKS_HOST=...
export DATABRICKS_CLIENT_ID=...
export DATABRICKS_CLIENT_SECRET=...
python -m lakeventory --source sdk --out-xlsx report.xlsx
# Upload report as artifact
```

### Use Case: Large Workspace (1M+ objects)
```bash
# Configure batching to avoid timeouts
python -m lakeventory \
  --source sdk \
  --out report.md \
  --batch-size 50 \
  --batch-sleep-ms 500
```

### Use Case: Specific Data Inventory
```bash
# Only catalog and security
make inventory-selective COLLECTORS=unity_catalog,security
```

### Use Case: Production Deployment
```bash
# Build minimal Docker image for deployment
docker build -f Dockerfile.static -t lakeventory:prod .
docker run --rm -v $(pwd)/.lakeventory:/app/.lakeventory:ro lakeventory:prod
```

---

## Version History

### v1.1.0 (2026-03-09)
- ✅ Multi-workspace support with interactive setup wizard
- ✅ YAML-based configuration
- ✅ Excel as default output format
- ✅ Per-workspace custom output directories
- ✅ Comprehensive multi-workspace documentation

### alpha (2026-03-09)
- ✅ Scheduled Docker Compose runner
- ✅ Three Docker variants (Alpine, Distroless, Static)
- ✅ Service Principal authentication
- ✅ Comprehensive documentation split into focused guides

---

## See Also

- [README.md](../README.md) - Project overview
- [AUTHENTICATION.md](AUTHENTICATION.md) - Authentication setup
- [PERMISSIONS.md](PERMISSIONS.md) - Required permissions
- [USAGE.md](USAGE.md) - Command reference
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues
- [DOCKER.md](DOCKER.md) - Docker deployment
- [CLI.md](CLI.md) - Installation options

---

**Last Updated:** 2026-03-12  
**Status:** All features documented in English ✅
