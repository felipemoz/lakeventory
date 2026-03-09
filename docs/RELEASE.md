# Release Notes

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
