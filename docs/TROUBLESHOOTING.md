# Troubleshooting Guide

## Authentication Issues

### Error: "Missing DATABRICKS_HOST"
**Solution:** Set `DATABRICKS_HOST` in `.env` or environment variable
```bash
export DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
```

### Error: "Missing Databricks credentials"
**Solution:** Configure one of these authentication methods:
```env
# Option 1: Service Principal (recommended)
DATABRICKS_CLIENT_ID=...
DATABRICKS_CLIENT_SECRET=...

# Option 2: PAT Token
DATABRICKS_TOKEN=...

# Option 3: Username + Password
DATABRICKS_USERNAME=...
DATABRICKS_PASSWORD=...
```

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
3. Run `python -m lakeventory --validate-permissions` to check access
4. Enable debug logging: `--log-level debug`
5. Open an issue with debug output and error message
