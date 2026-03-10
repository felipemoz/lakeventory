# Permissions Guide

## Multi-Workspace Permissions

When using multi-workspace configuration, each workspace can have:
- Different authentication methods (PAT, Service Principal)
- Different user permissions
- Different API access

**Test permissions per workspace:**
```bash
# Test specific workspace
python -m lakeventory --workspace prod --validate-permissions

# Test all workspaces
python -m lakeventory --all-workspaces --validate-permissions
```

**See [MULTI_WORKSPACE.md](MULTI_WORKSPACE.md)** for workspace setup.

---

## Health Check (Before Starting)

Verify that everything is properly configured:

```bash
make check
```

This performs 4 verification steps:

1. **Python Version**: Checks that Python 3.8+ is installed
2. **Dependencies**: Verifies `databricks-sdk`, `openpyxl`, and `tqdm` are installed
3. **Credentials**: Validates `DATABRICKS_HOST` and authentication (detects auth method automatically)
4. **Workspace Connection**: Connects to the workspace and verifies access

### Example Successful Check

```
======================================================================
INVENTORY TOOL HEALTH CHECK
======================================================================

[1/4] Python Version
  Python 3.9.6
  ✅ PASS (Python 3.8+)

[2/4] Dependencies
  ✅ databricks-sdk
  ✅ openpyxl
  ✅ tqdm

[3/4] Databricks Credentials
  ✅ DATABRICKS_HOST: https://dbc-abc123.cloud.databricks.com
  ✅ DATABRICKS_TOKEN: configured
  ✅ Cloud Provider: AZURE

[4/4] Workspace Connection
  Connecting to workspace...
  ✅ Connected to workspace ID: 1234567890
  ✅ Can list workspace objects

======================================================================
✅ ALL CHECKS PASSED - READY TO RUN INVENTORY
======================================================================
```

---

## Required Permissions

The user running this inventory script needs specific API permissions to access workspace assets.

### Minimum Required Permissions

| API Group | Required Permissions | Collectors Affected |
|-----------|----------------------|---------------------|
| **Workspace** | `workspace:read` | workspace |
| **Jobs** | `jobs:read` | jobs |
| **Clusters** | `clusters:read` | clusters |
| **SQL** | `sql:read` | sql |
| **MLflow** | `experiments:read` | mlflow |
| **Unity Catalog** | `catalogs:read`, `schemas:read`, `tables:read`, `volumes:read`, `external_locations:read` | unity_catalog |
| **Repos** | `repos:read` | repos |
| **Secrets** | `secrets:read` | security |
| **Identities** | `users:read`, `groups:read`, `service_principals:read` | identities |
| **Serving** | `serving_endpoints:read`, `vector_search_endpoints:read` | serving |
| **Sharing** | `shares:read` | sharing |
| **DBFS** | `dbfs:read` (if `--include-dbfs` is used) | dbfs |

### Recommended Role

```json
{
  "name": "inventory_reader",
  "permissions": [
    "workspace:read",
    "jobs:read",
    "clusters:read",
    "sql:read",
    "experiments:read",
    "catalogs:read",
    "schemas:read",
    "tables:read",
    "volumes:read",
    "external_locations:read",
    "repos:read",
    "secrets:read",
    "users:read",
    "groups:read",
    "service_principals:read",
    "serving_endpoints:read",
    "vector_search_endpoints:read",
    "shares:read"
  ]
}
```

---

## Validate Permissions (Before Running)

Before running the full inventory, validate that your user has the required permissions:

```bash
python -m lakeventory --validate-permissions --source sdk
```

This will:
- Connect to the Databricks workspace
- Test access to each API endpoint
- Print a detailed permission validation report
- **Fail with exit code 1 if any permissions are missing**

### Example Permission Report

```
======================================================================
PERMISSION VALIDATION REPORT
======================================================================

✅ PASSED: 11/11 permission checks

Core APIs (Required):
  ✅ Workspace
  ✅ Jobs
  ✅ Clusters
  ✅ Sql
  ✅ Mlflow
  ✅ Unity Catalog
  ✅ Repos
  ✅ Security
  ✅ Identities
  ✅ Serving
  ✅ Sharing

======================================================================
```

### Handle Missing Permissions

```
======================================================================
PERMISSION VALIDATION REPORT
======================================================================

✅ PASSED: 9/11 permission checks

⚠️  clusters.list: 403 Forbidden - User does not have permission
⚠️  catalogs.list: 403 Forbidden - User does not have permission

======================================================================
```

### Makefile Targets

```bash
# Validate permissions and exit on error
make inventory-validate

# Run full inventory (with automatic permission validation)
make inventory

# Skip validation (not recommended)
make inventory --skip-validation
```

---

## Cloud-Specific Considerations

- **AWS**: Instance Profiles API requires additional AWS IAM permissions
- **Azure**: Instance Profiles not available (uses Managed Identities)
- **GCP**: Instance Profiles not available (uses Service Accounts)

Set `DATABRICKS_CLOUD_PROVIDER` to help the script skip non-applicable APIs:

```env
DATABRICKS_CLOUD_PROVIDER=AZURE  # or AWS, GCP
```
