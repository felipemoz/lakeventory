# Authentication Guide

The tool supports **3 authentication methods** (in order of priority):

## 1️⃣ Service Principal (Recommended for Production/CI-CD)

Best for automation, CI/CD pipelines, and scheduled jobs.

### Create a Service Principal

1. Go to Databricks Admin Console → Identity & Access → Service Principals
2. Click "Add Service Principal" and create with name (e.g., "inventory-reader")
3. Assign required permissions (read-only access to workspace APIs)
4. Create a PAT (Personal Access Token) for the Service Principal

### Configure in `.env`

```env
DATABRICKS_HOST=https://<workspace-host>
DATABRICKS_CLIENT_ID=<service-principal-id>
DATABRICKS_CLIENT_SECRET=<service-principal-secret>
```

**Advantages:**
- ✅ Secure for production and CI/CD (no personal credentials)
- ✅ Easily rotatable (create new, deprecate old)
- ✅ Full auditability (logs show which SP did what)
- ✅ Can restrict permissions per SP

### Setup for CI/CD

**GitHub Actions:**
```yaml
name: Run Lakeventory
on: [push]

jobs:
  inventory:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Inventory
        env:
          DATABRICKS_HOST: ${{ secrets.DATABRICKS_HOST }}
          DATABRICKS_CLIENT_ID: ${{ secrets.SP_CLIENT_ID }}
          DATABRICKS_CLIENT_SECRET: ${{ secrets.SP_CLIENT_SECRET }}
        run: python -m lakeventory --source sdk
```

**Jenkins/GitLab CI:**
```bash
export DATABRICKS_HOST="https://your-workspace.cloud.databricks.com"
export DATABRICKS_CLIENT_ID="a1b2c3d4-e5f6-7890-1234-567890abcdef"
export DATABRICKS_CLIENT_SECRET="<secret-from-secure-storage>"
python -m lakeventory --source sdk
```

### Verify Access

```bash
# Check which auth method is detected
python -m lakeventory --log-level debug --root . 2>&1 | grep "authentication method"
# Output: INFO Detected authentication method: Service Principal (Client ID: a1b2c3d4...)

# Run health check
make check
# Will show: ✅ DATABRICKS_CLIENT_ID: configured
```

---

## 2️⃣ PAT Token (for Development/Testing)

Personal Access Token from your Databricks account.

### Create a PAT

1. In Databricks, click your profile → User Settings → Access tokens
2. Click "Generate new token" → Copy the token

### Configure in `.env`

```env
DATABRICKS_HOST=https://<workspace-host>
DATABRICKS_TOKEN=<your-pat-token>
```

**Advantages:**
- ✅ Easy to set up for development
- ✅ Tied to your user account
- ✅ Customizable expiration (7 days to 90 years)

---

## 3️⃣ Username + Password (Basic Auth)

Use your Databricks username and password.

### Configure in `.env`

```env
DATABRICKS_HOST=https://<workspace-host>
DATABRICKS_USERNAME=<your-username>
DATABRICKS_PASSWORD=<your-password>
```

⚠️ **Not recommended** for production or CI/CD. Use Service Principal instead.

---

## Priority & Automatic Detection

The tool **automatically detects** which authentication method is configured:

```
1. Service Principal (DATABRICKS_CLIENT_ID + DATABRICKS_CLIENT_SECRET) ← Highest Priority
2. PAT Token (DATABRICKS_TOKEN)
3. Basic Auth (DATABRICKS_USERNAME + DATABRICKS_PASSWORD) ← Lowest Priority
```

The first one found will be used. If multiple are configured, only the highest priority will be used.

### Debug Auth Detection

```bash
python -m lakeventory --log-level debug 2>&1 | grep -i "authentication"
```
