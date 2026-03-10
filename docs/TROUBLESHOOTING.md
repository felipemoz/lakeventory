# Troubleshooting Guide

## Multi-Workspace Issues

### Error: "No workspaces configured"
**Solution:** Run the setup wizard:
```bash
make setup
# or: python -m lakeventory setup
```

### Error: "Workspace 'xyz' not found in configuration"
**Solution:** List available workspaces:
```bash
make list-workspaces
# or: python -m lakeventory --list-workspaces
```

Then use one of the listed workspace names:
```bash
make inventory-workspace WORKSPACE=prod
```

### Different permissions across workspaces
**Cause:** Each workspace may have different RBAC settings  
**Solution:** Validate permissions per workspace:
```bash
python -m lakeventory --workspace prod --validate-permissions
python -m lakeventory --workspace staging --validate-permissions
```

### Custom output directories not working
**Check:** Verify workspace configuration in `.lakeventory/config.yaml`:
```yaml
workspaces:
  prod:
    output_dir: /custom/path  # Must be absolute or relative path
```

**See [MULTI_WORKSPACE.md](MULTI_WORKSPACE.md)** for complete configuration guide.

---

## Authentication Issues

### Error: "Missing DATABRICKS_HOST"
**Solution:** Configure o workspace em `.lakeventory/config.yaml`:
```bash
make setup
```

Ou defina temporariamente via env var para debug:
```bash
export DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
```

### Error: "Missing Databricks credentials"
**Solution (Single Workspace):** Configure one of these authentication methods:
```env
# Option 1: Service Principal (recommended)
DATABRICKS_CLIENT_ID=...
DATABRICKS_CLIENT_SECRET=...

# Option 2: PAT Token
DATABRICKS_TOKEN=...
```

**Solution (Multi-Workspace):** Use setup wizard:
```bash
make setup
```

**See [AUTHENTICATION.md](AUTHENTICATION.md)** for detailed authentication guide.

### Error: "Authentication failed (401)"
**Solution:** Verify credentials are correct and not expired. For PAT tokens, check expiration date.

---

## Permission Issues

### Error: "403 Forbidden" on specific API
**Solution:** Run permission validation to identify missing permissions:
```bash
python -m lakeventory --validate-permissions --source sdk
```
See [PERMISSIONS.md](PERMISSIONS.md) for required permissions.

### Some data missing in report
**Cause:** User lacks permissions for certain APIs  
**Solution:** Check the `Warnings` sheet in Excel or run:
```bash
python -m lakeventory --log-level debug 2>&1 | grep "not available"
```

---

## Timeout Issues

### Error: "Request timed out"
**Cause:** Workspace is too large or network is slow  
**Solution:** Use batching to reduce API call volume:
```bash
python -m lakeventory \
  --source sdk \
  --batch-size 50 \
  --batch-sleep-ms 500
```

**Tips:**
- Reduce `--batch-size` for larger workspaces
- Increase `--batch-sleep-ms` if timeout persists
- Skip heavy collectors with `--include-runs` and `--include-dbfs`

### Error: "List results truncated"
**Cause:** API timeout during large list operations  
**Solution:** Add batching and sleep:
```bash
python -m lakeventory \
  --source sdk \
  --batch-size 100 \
  --batch-sleep-ms 1000
```

---

## Performance Issues

### Script is running slowly
**Cause:** Default settings not optimized for large workspaces  
**Solution:**
1. Skip unnecessary heavy collectors:
   ```bash
  python -m lakeventory \
     --source sdk \
     --skip-heavy-collectors
   # or exclude specific ones
   --collectors workspace,jobs,sql
   ```

2. Use batching:
   ```bash
  python -m lakeventory \
     --source sdk \
     --batch-size 100 \
     --batch-sleep-ms 200
   ```

3. Disable progress bars:
   ```bash
  INVENTORY_PROGRESS=0 python -m lakeventory --source sdk --out report.md
   ```

---

## Cloud-Specific Issues

### Error: "Instance profiles not available"
**Cause:** Running on Azure/GCP where Instance Profiles don't exist  
**Solution:** Set cloud provider:
```env
DATABRICKS_CLOUD_PROVIDER=AZURE
```
or
```bash
export DATABRICKS_CLOUD_PROVIDER=GCP
```

Valid values: `AWS`, `AZURE`, `GCP`

---

## Output Issues

### Files are in Markdown instead of Excel
**Cause:** Output format might be misconfigured  
**Solution:** Check your configuration:
```yaml
# .lakeventory/config.yaml
global_config:
  output_format: xlsx  # Should be xlsx for Excel (default)
```

Or specify format explicitly:
```bash
python -m lakeventory --out-xlsx report.xlsx
```

### Want to change default output format
**Solution:** Edit `.lakeventory/config.yaml`:
```yaml
global_config:
  output_format: xlsx      # Default: Excel
  # output_format: markdown  # Alternative: Markdown
  # output_format: json      # Alternative: JSON
  # output_format: all       # All formats
```

### Error: "Output directory not found"
**Solution:** Ensure directory exists or is accessible:
```bash
python -m lakeventory \
  --source sdk \
  --out-dir ./my-reports \
  --out report.md
```

### Excel file is corrupted
**Solution:** Regenerate the file:
```bash
python -m lakeventory \
  --source sdk \
  --out-xlsx report.xlsx
```

If problem persists, check disk space and permissions.

---

## Dependency Issues

### Error: "ModuleNotFoundError: No module named 'databricks'"
**Solution:** Install dependencies:
```bash
pip install -r requirements.txt
```

### Error: "ImportError: openpyxl"
**Solution:** Install openpyxl:
```bash
pip install openpyxl
```

### Python version mismatch
**Check:** `python3 --version` (requires Python 3.8+)  
**Solution:** Use Python 3.8 or higher

---

## Debug Mode

### Enable detailed logging
```bash
python -m lakeventory \
  --source sdk \
  --log-level debug \
  --out report.md 2>&1 | tee debug.log
```

### Check which endpoints are being called
```bash
python -m lakeventory \
  --log-level debug 2>&1 | grep "workspace.list\|jobs.list\|clusters.list"
```

### Identify permission failures
```bash
python -m lakeventory \
  --log-level debug 2>&1 | grep "403\|Forbidden\|not available"
```

---

## Still Having Issues?

1. Check the `Warnings` sheet in Excel output for API errors
2. Run `make check` to verify environment setup
3. Review documentation:
   - [MULTI_WORKSPACE.md](MULTI_WORKSPACE.md) - Multi-workspace configuration
   - [AUTHENTICATION.md](AUTHENTICATION.md) - Authentication methods
   - [PERMISSIONS.md](PERMISSIONS.md) - Required permissions
   - [USAGE.md](USAGE.md) - Command reference
4. Enable debug logging: `--log-level debug`
5. Check GitHub issues: https://github.com/felipemoz/lakeventory/issues
3. Run `python -m lakeventory --validate-permissions` to check access
4. Enable debug logging: `--log-level debug`
5. Open an issue with debug output and error message
