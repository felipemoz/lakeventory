"""Health check for inventory tool: dependencies, auth, and workspace."""

import sys
import os
from pathlib import Path
from itertools import islice


def run_health_check():
    """Run all health checks and print results."""
    # Try to import required packages
    print("=" * 70)
    print("INVENTORY TOOL HEALTH CHECK")
    print("=" * 70)
    print()

    # 1. Check Python version
    print("[1/4] Python Version")
    print(f"  Python {sys.version.split()[0]}")
    if sys.version_info >= (3, 8):
        print("  ✅ PASS (Python 3.8+)")
    else:
        print("  ❌ FAIL (requires Python 3.8+)")
        return False
    print()

    # 2. Check dependencies
    print("[2/4] Dependencies")
    deps = {
        "databricks.sdk": "databricks-sdk",
        "openpyxl": "openpyxl",
        "tqdm": "tqdm",
    }

    missing_deps = []
    for module_name, package_name in deps.items():
        try:
            __import__(module_name)
            print(f"  ✅ {package_name}")
        except ImportError:
            print(f"  ❌ {package_name} (not installed)")
            missing_deps.append(package_name)

    if missing_deps:
        print()
        print(f"  Missing: {', '.join(missing_deps)}")
        print(f"  Run: pip install {' '.join(missing_deps)}")
        return False
    print()

    # 3. Check Databricks credentials
    print("[3/4] Databricks Credentials")
    host = os.getenv("DATABRICKS_HOST", "").strip()
    token = os.getenv("DATABRICKS_TOKEN", "").strip()
    username = os.getenv("DATABRICKS_USERNAME", "").strip()
    password = os.getenv("DATABRICKS_PASSWORD", "").strip()

    if not host:
        print("  ❌ DATABRICKS_HOST not set")
        return False
    else:
        print(f"  ✅ DATABRICKS_HOST: {host}")

    if token or (username and password):
        if token:
            print(f"  ✅ DATABRICKS_TOKEN: configured")
        else:
            print(f"  ✅ DATABRICKS_USERNAME/PASSWORD: configured")
    else:
        print("  ❌ No authentication configured (need DATABRICKS_TOKEN or USERNAME/PASSWORD)")
        return False

    cloud_provider = os.getenv("DATABRICKS_CLOUD_PROVIDER", "").upper() or "AUTO"
    print(f"  ✅ Cloud Provider: {cloud_provider}")
    print()

    # 4. Check workspace connection
    print("[4/4] Workspace Connection")
    try:
        from databricks.sdk import WorkspaceClient
        
        print("  Connecting to workspace...")
        client = WorkspaceClient(
            host=host,
            token=token if token else None,
            username=username if username else None,
            password=password if password else None,
        )
        
        # Try to get workspace info
        workspace_id = client.workspace.get_status(path="/").workspace_id
        print(f"  ✅ Connected to workspace ID: {workspace_id}")
        
        # Try a simple API call to verify access
        list(islice(client.workspace.list(path="/"), 1))
        print(f"  ✅ Can list workspace objects")
        
    except Exception as e:
        print(f"  ❌ Connection failed: {str(e)}")
        return False

    print()
    print("=" * 70)
    print("✅ ALL CHECKS PASSED - READY TO RUN INVENTORY")
    print("=" * 70)
    print()
    print("Next steps:")
    print("  1. Run: make inventory-validate")
    print("     (to validate API permissions)")
    print("  2. Run: make inventory")
    print("     (to generate workspace inventory)")
    print()
    
    return True


if __name__ == "__main__":
    success = run_health_check()
    sys.exit(0 if success else 1)
