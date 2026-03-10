# Release Notes

## Release 1.1.0 (2026-03-09) 🎉

**Tag:** v1.1.0  
**Type:** Feature Release

### Summary
Major feature release adding **multi-workspace support** with interactive setup wizard, workspace-specific configurations, and enhanced authentication options.

### Highlights
- 🆕 **Multi-workspace management** - Configure and manage multiple Databricks workspaces
- 🎯 **Interactive setup wizard** - Easy workspace configuration via `make setup`
- 📊 **Excel as default format** - Changed from Markdown to XLSX for better usability

- 📁 **Custom output directories per workspace** - Override output location per workspace
- 🔄 **Batch workspace operations** - Run inventory on all workspaces with single command

### Changes
**Added**
- Multi-workspace configuration manager (`workspace_config.py`)
- Interactive setup wizard (`setup_wizard.py`)
- YAML-based configuration (`.lakeventory/config.yaml`)
- CLI flags: `--workspace`, `--all-workspaces`, `--list-workspaces`
- Makefile targets: `setup`, `list-workspaces`, `inventory-workspace`, `inventory-all`
- Per-workspace output directory configuration
- Configuration template (`.lakeventory/config.yaml.example`)
- Comprehensive multi-workspace documentation (`docs/MULTI_WORKSPACE.md`)

**Changed**
- Default output format: `markdown` → `xlsx` (Excel)
- Documentation updated across all guides with multi-workspace examples
- Authentication methods: Service Principal and PAT only (removed Basic Auth)
- Output organization: workspace-specific subdirectories
- SDK compatibility fixes for ObjectInfo variations

**Fixed**
- WorkspaceClient initialization with correct kwargs
- workspace_id AttributeError handling with fallbacks
- getpass paste issues with environment variable fallback
- Health check workspace_id retrieval

**Removed**
- Basic Auth (username/password) support
- Azure CLI authentication (cloud lock-in)

### Breaking Changes
- Default output format changed from Markdown to Excel/XLSX
- Basic Auth and Azure CLI no longer supported (use PAT or Service Principal)
- Configuration file structure changed (migrates automatically from `.env`)

### Migration Notes
**From Single to Multi-Workspace:**
```bash
# Run setup wizard - automatically migrates from .env
make setup

# Old .env configuration is preserved as "default" workspace
# Add more workspaces through the wizard
```

**Format Change:**
- Excel (XLSX) is now the default output format
- To continue using Markdown, set in config.yaml:
  ```yaml
  global_config:
    output_format: markdown
  ```

### Documentation Updates
- Updated README with multi-workspace quick start
- Added comprehensive MULTI_WORKSPACE.md guide
- Updated AUTHENTICATION.md focusing on PAT and Service Principal
- Enhanced USAGE.md with multi-workspace commands
- Added troubleshooting for multi-workspace scenarios
- Updated all examples to show multi-workspace usage

### Security
- Secrets stored in `.lakeventory/config.yaml` (added to .gitignore)
- Support for environment variable secrets (CI/CD friendly)
- Service Principal recommended for production (no personal credentials)

### Tests
- All existing tests pass
- Added test scripts for multi-workspace scenarios

### Known Issues
- Terminal paste issues with getpass in some environments (workaround: use env vars)

---

## Release alpha (2026-03-09)

**Tag:** alpha  
**Type:** alpha

### Summary
First public alpha for Lakeventory with scheduled runs and updated branding.

### Highlights
- Lakeventory package rename and CLI usage (`python -m lakeventory`)
- Scheduled container runner with full-first then incremental mode
- Docker Compose with `.env` loading and named volumes for output/cache
- Service Principal authentication support and auto-detection
- Makefile parameter support for `OUTPUT_DIR`
- Comprehensive docs split into focused guides
- Contributors guide and MIT license

### Changes
**Added**
- Docker Compose scheduled runner (full-first, then incremental)
- Dockerfile + runner script (`scripts/run_scheduled.sh`)
- `.env` support in compose via `env_file`
- Named volumes for output and cache persistence
- Release notes template in `docs/RELEASE.md`
- Contributors guide (`CONTRIBUTORS.md`) and MIT `LICENSE`
- Service Principal auth path and auto-detection
- Output directory parameterization in Makefile (`OUTPUT_DIR`)

**Changed**
- Report title now uses Lakeventory branding
- Package imports and CLI commands updated to `lakeventory`
- Docker Compose now loads env vars from `.env`
- Docs reorganized into focused guides (auth, permissions, usage, troubleshooting)

**Fixed**
- N/A

**Removed**
- N/A

### Breaking Changes
- Package import path changed from `databricks_inventory` to `lakeventory`

### Migration Notes
- Update imports to `lakeventory` in custom scripts/tests
- Use `python -m lakeventory` instead of `python -m databricks_inventory`
- If using Compose, set variables in `.env` or `docker-compose.yml`

### Security
- N/A

### Tests
- `pytest -q`

### Known Issues
- None reported
