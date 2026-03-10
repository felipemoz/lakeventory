# Multi-Workspace Support

Lakeventory now supports managing multiple Databricks workspaces from a single configuration file!

## Quick Start

### 1. Interactive Setup

Run the setup wizard to configure your workspaces:

```bash
make setup
# or
python -m lakeventory setup
```

The wizard will guide you through:
- Adding workspaces (dev, staging, prod, etc.)
- Configuring authentication (PAT, Service Principal)
- Testing connections
- Setting a default workspace

If your shell hangs when pasting tokens, you can set secrets via env vars before running the wizard:

```bash
export DATABRICKS_TOKEN="dapi..."                  # PAT
export DATABRICKS_CLIENT_SECRET="..."             # Service Principal
python -m lakeventory setup
```

### 2. List Configured Workspaces

```bash
make list-workspaces
# or
python -m lakeventory --list-workspaces
```

Output:
```
Name            Host                                      Auth Method
─────────────────────────────────────────────────────────────────────
prod *          adb-3456789.13.azuredatabricks.net        pat
staging         adb-2345678.13.azuredatabricks.net        service_principal

* = default workspace
```

### 3. Run Inventory

#### On default workspace:
```bash
make inventory
# or
python -m lakeventory
```

#### On specific workspace:
```bash
make inventory-workspace WORKSPACE=dev
# or
python -m lakeventory --workspace dev
# or
python -m lakeventory -w staging
```

#### On all workspaces:
```bash
make inventory-all
# or
python -m lakeventory --all-workspaces
```

## Configuration File

Configuration is stored in `.lakeventory/config.yaml`:

```yaml
version: "1.0"

# Default workspace when not specified
default_workspace: prod

# Workspace configurations
workspaces:
  prod:
    host: https://adb-3456789.13.azuredatabricks.net
    auth_method: pat
    token: dapi...
    description: Production environment
    # output_dir: /custom/path  # Optional: Override global output_dir
  
  staging:
    host: https://adb-2345678.13.azuredatabricks.net
    auth_method: service_principal
    client_id: xxxx-xxxx-xxxx
    client_secret: yyyy
    tenant_id: zzzz-zzzz-zzzz
    description: Staging environment
    output_dir: ./staging-reports  # Example: Custom output directory

# Global settings
global_config:
  output_dir: ./output  # Default output directory
  output_format: xlsx   # markdown, json, xlsx, all
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

### Configuration Options

**Per-Workspace Settings:**
- `host`: Databricks workspace URL (required)
- `auth_method`: Authentication method - `pat` or `service_principal` (required)
- `description`: Human-readable description (optional)
- `output_dir`: Custom output directory for this workspace (optional, overrides global)
- `token`: PAT token for `pat` auth (required for PAT)
- `client_id`, `client_secret`, `tenant_id`: For Service Principal auth (required for SP)

**Global Settings:**
- `output_dir`: Base output directory (default: `./output`)
  - Each workspace gets a subdirectory: `{output_dir}/{workspace_name}/`
  - Can be overridden per-workspace with workspace-specific `output_dir`
- `output_format`: Output format - `markdown`, `json`, `xlsx`, or `all` (default: `xlsx`)
- `batch_size`: Items per batch before sleeping (default: 200)
- `batch_sleep_ms`: Sleep between batches in milliseconds (default: 50)
- `include_runs`: Include job run history (default: false)
- `include_query_history`: Include SQL query history (default: false)
- `include_dbfs`: Include DBFS root listing (default: false)
- `enabled_collectors`: List of collectors to run (default: all)

## Authentication Methods

### 1. Personal Access Token (PAT)

**Best for:** Testing, personal use

```yaml
auth_method: pat
token: dapi...
```

Create PAT at: Workspace Settings → Developer → Access Tokens

### 2. Service Principal (OAuth)

**Best for:** Production, CI/CD pipelines

```yaml
auth_method: service_principal
client_id: xxxx-xxxx-xxxx
client_secret: yyyy
tenant_id: zzzz-zzzz-zzzz
```

## Output Structure

When using multi-workspace, outputs are organized by workspace:

```
output/                    # Default global output_dir
├── dev/
│   ├── workspace_1234567_20260309_1422.xlsx
│   └── .inventory_cache/
├── staging/               # Custom: staging-reports/staging/ if output_dir overridden
│   ├── workspace_2345678_20260309_1423.xlsx
│   └── .inventory_cache/
└── prod/
    ├── workspace_3456789_20260309_1424.xlsx
    └── .inventory_cache/
```

Each workspace gets its own subdirectory under the configured `output_dir` (global or workspace-specific):
- Global: `{global_config.output_dir}/{workspace_name}/`
- Custom: `{workspace.output_dir}/{workspace_name}/`

## Serverless Workspace Support

For serverless workspaces (no cluster management):

```bash
# Single workspace
make inventory-workspace WORKSPACE=serverless SERVERLESS=1

# All workspaces in serverless mode
make inventory-all SERVERLESS=1
```

## Migration from .env

If you have an existing `.env` file, the setup wizard will offer to migrate it automatically:

```bash
$ make setup

📋 Found existing .env configuration
Would you like to migrate to multi-workspace config? [Y/n]: Y

✅ Migrated configuration as 'default' workspace
   You can now add more workspaces!
```

## Advanced Usage

### Custom Output Directory per Workspace

```bash
python -m lakeventory -w prod --out-dir ./reports/production
```

### Selective Collectors

```bash
python -m lakeventory -w dev --collectors workspace,jobs,clusters
```

### Incremental Mode (Delta Only)

```bash
python -m lakeventory -w prod --incremental
```

### Debug Specific Workspace

```bash
python -m lakeventory -w staging --log-level debug
```

## Troubleshooting

### "No workspace specified and no default configured"

**Solution:** Run `make setup` to configure at least one workspace, or set environment variables:

```bash
export DATABRICKS_HOST=https://...
export DATABRICKS_TOKEN=dapi...
python -m lakeventory
```

### "Workspace 'xxx' not found in configuration"

**Solution:** Check workspace name:

```bash
make list-workspaces
```

### Connection Test Fails

During setup, if connection test fails:
1. Verify URL is correct (include `https://`)
2. Check authentication credentials
3. Verify network access to workspace
4. For Service Principal: ensure Client ID, Secret, and Tenant ID are correct

### Multiple Authentication Methods

You can mix authentication methods across workspaces:
- `prod` → Service Principal (secure, automated)
- `staging` → Service Principal (team testing, secure)
- `dev` → PAT (personal development, quick access)

## Security Best Practices

1. **Never commit `.lakeventory/config.yaml` to git** (contains secrets)
   - Already in `.gitignore`

2. **Use Service Principals for production**
   - Better audit trail
   - Can be rotated without user impact

3. **Limit PAT lifetime**
   - Set expiration dates
   - Rotate regularly

4. **Use environment variables for CI/CD**
   - Export DATABRICKS_TOKEN or Service Principal credentials
   - Never commit secrets to version control

## Next Steps

- [Permissions Guide](PERMISSIONS.md)
- [Troubleshooting](TROUBLESHOOTING.md)
- [CI/CD Integration](CICD.md)
