# CLI Installation and Usage Guide

## Installation Methods

### Method 1: Install from Source (Editable)

For development or local use:

```bash
# Clone the repository
git clone https://github.com/felipemoz/lakeventory.git
cd lakeventory

# Install in editable mode
pip install -e .

# Now you can use 'lakeventory' command directly
lakeventory --version
```

### Method 2: Install from PyPI (Future)

Once published to PyPI:

```bash
pip install lakeventory
lakeventory --version
```

### Method 3: Standalone Executable

Build a single executable file (no Python required):

```bash
# Install PyInstaller
pip install pyinstaller

# Build executable
bash scripts/build_executable.sh

# Use the executable
./dist/lakeventory version
```

The executable can be distributed to machines without Python installed.

---

## CLI Commands

### Global Options

```bash
lakeventory --help              # Show help
lakeventory --version           # Show version
lakeventory --verbose           # Enable verbose output
lakeventory --debug             # Enable debug logging
```

### Subcommands

#### 1. collect - Run Inventory Collection

Basic usage:
```bash
lakeventory collect --out report.md
```

With Excel output:
```bash
lakeventory collect --out report.md --out-xlsx report.xlsx
```

Incremental mode (only changes):
```bash
lakeventory collect --incremental --out changes.md
```

Include additional data:
```bash
lakeventory collect \
  --out report.md \
  --include-runs \
  --include-query-history \
  --include-dbfs
```

Specific categories only:
```bash
lakeventory collect \
  --out report.md \
  --categories jobs clusters warehouses
```

Custom cache and output directories:
```bash
lakeventory collect \
  --out report.md \
  --cache-dir /path/to/cache \
  --output-dir /path/to/output
```

#### 2. cache - Manage Snapshots

List cached snapshots:
```bash
lakeventory cache list
lakeventory cache list --cache-dir /custom/cache
```

Clear cache:
```bash
lakeventory cache clear
lakeventory cache clear --force  # No confirmation
```

#### 3. diff - Compare Inventories

Compare two inventory files:
```bash
lakeventory diff --baseline old.md --current new.md
lakeventory diff --baseline old.md --current new.md --verbose
```

#### 4. version - Show Version Info

```bash
lakeventory version
lakeventory version --verbose  # Show Python and SDK versions
```

---

## Environment Variables

Use these only as optional one-off overrides:

```bash
export DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
export DATABRICKS_TOKEN=dapi...
```

> **Recommended:** configure credentials in `.lakeventory/config.yaml` with `make setup`.

---

## Examples

### Example 1: Daily Audit Report

```bash
# Full inventory with Excel export
lakeventory collect \
  --out daily_audit.md \
  --out-xlsx daily_audit.xlsx \
  --timestamp
```

### Example 2: Change Tracking

```bash
# First run: full inventory (creates cache)
lakeventory collect --out baseline.md

# Later: incremental run (shows only changes)
lakeventory collect --incremental --out changes.md
```

### Example 3: Focused Collection

```bash
# Collect only specific categories
lakeventory collect \
  --out security_audit.xlsx \
  --categories tokens secrets ip_access_lists identities
```

### Example 4: Cache Management

```bash
# List all snapshots
lakeventory cache list

# Clear old snapshots
lakeventory cache clear --force
```

### Example 5: Compare Two Workspaces

```bash
# Configure workspaces in .lakeventory/config.yaml (or via `make setup`), then run:
lakeventory -w workspace-a --out workspace_a.md
lakeventory -w workspace-b --out workspace_b.md

# Compare
lakeventory diff --baseline workspace_a.md --current workspace_b.md --verbose
```

---

## Makefile Integration

The project includes Makefile targets for convenience:

```bash
make install       # Install package
make inventory     # Run basic inventory
make check         # Verify setup
make test          # Run tests
```

---

## Docker Usage

Run in Docker:

```bash
docker build -t lakeventory .
docker run --rm -v $(pwd)/.lakeventory:/app/.lakeventory:ro lakeventory collect --out report.md
```

With docker-compose:

```bash
# Monte o .lakeventory com config.yaml e suba o container
docker-compose up -d
```

---

## Troubleshooting

**Command not found after installation:**
```bash
# Ensure pip bin directory is in PATH
export PATH="$HOME/.local/bin:$PATH"

# Or reinstall
pip install --force-reinstall -e .
```

**ModuleNotFoundError:**
```bash
# Reinstall dependencies
pip install -r requirements.txt
pip install -e .
```

**Permissions errors:**
```bash
# Use user installation
pip install --user -e .
```

---

## Distribution

### Share as Package

```bash
# Build wheel
python -m build

# Share dist/lakeventory-1.0.0-py3-none-any.whl
pip install lakeventory-1.0.0-py3-none-any.whl
```

### Share as Executable

```bash
# Build executable
bash scripts/build_executable.sh

# Share dist/lakeventory (Linux/Mac) or dist/lakeventory.exe (Windows)
# No Python installation required on target machine
```

---

## Next Steps

- See [docs/USAGE.md](USAGE.md) for detailed usage examples
- See [docs/AUTHENTICATION.md](AUTHENTICATION.md) for auth configuration
- See [docs/PERMISSIONS.md](PERMISSIONS.md) for required permissions
- See [docs/TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues
