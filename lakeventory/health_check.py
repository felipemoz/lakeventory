"""Health check for Lakeventory using config.yaml workspace settings."""

import argparse
import re
import sys
from itertools import islice
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import urlparse

from databricks.sdk import WorkspaceClient

from lakeventory.workspace_config import ConfigManager, WorkspaceConfig


CONFIG_MANAGER = ConfigManager()


def _extract_workspace_id(host: str) -> str:
    if not host:
        return "workspace"
    parsed = urlparse(host)
    hostname = parsed.hostname or host
    match = re.search(r"adb-(\d+)", hostname)
    if match:
        return match.group(1)
    match = re.search(r"dbc-([a-z0-9-]+)", hostname)
    if match:
        return match.group(1)
    return hostname or "workspace"


def _build_client(workspace: WorkspaceConfig) -> WorkspaceClient:
    if workspace.auth_method == "service_principal":
        if not workspace.client_id or not workspace.client_secret:
            raise RuntimeError(
                "Service Principal incompleto no config.yaml: faltando client_id e/ou client_secret"
            )
        return WorkspaceClient(
            host=workspace.host,
            client_id=workspace.client_id,
            client_secret=workspace.client_secret,
        )

    if workspace.auth_method == "pat":
        if not workspace.token:
            raise RuntimeError("PAT incompleto no config.yaml: faltando token")
        return WorkspaceClient(host=workspace.host, token=workspace.token)

    raise RuntimeError(
        f"Método de autenticação não suportado no config.yaml: {workspace.auth_method}"
    )


def _load_workspace(workspace_name: Optional[str] = None) -> Tuple[Optional[WorkspaceConfig], Path]:
    config = CONFIG_MANAGER.load()
    config_path = CONFIG_MANAGER.config_path.resolve()

    if not config.workspaces:
        return None, config_path

    workspace = config.get_workspace(workspace_name)
    return workspace, config_path


def run_health_check(workspace_name: Optional[str] = None) -> bool:
    """Run all health checks and print results."""
    print("=" * 70)
    print("LAKEVENTORY HEALTH CHECK")
    print("=" * 70)
    print()

    print("[1/4] Python Version")
    print(f"  Python {sys.version.split()[0]}")
    if sys.version_info >= (3, 8):
        print("  ✅ PASS (Python 3.8+)")
    else:
        print("  ❌ FAIL (requires Python 3.8+)")
        return False
    print()

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

    print("[3/4] Lakeventory Config")
    workspace, config_path = _load_workspace(workspace_name)
    if not workspace:
        if workspace_name:
            print(f"  ❌ Workspace '{workspace_name}' não encontrado em: {config_path}")
            print("  ℹ️  Run: make list-workspaces")
        else:
            print(f"  ❌ Nenhum workspace configurado em: {config_path}")
            print("  ℹ️  Run: make setup")
        return False

    print(f"  ✅ Config file: {config_path}")
    print(f"  ✅ Workspace: {workspace.name}")
    print(f"  ✅ Host: {workspace.host}")
    print(f"  ✅ Auth Method: {workspace.auth_method}")

    if workspace.auth_method == "pat":
        if not workspace.token:
            print("  ❌ Token PAT ausente no config.yaml")
            return False
        print("  ✅ PAT token: configured")
    elif workspace.auth_method == "service_principal":
        missing = [
            field_name
            for field_name, value in {
                "client_id": workspace.client_id,
                "client_secret": workspace.client_secret,
            }.items()
            if not value
        ]
        if missing:
            print(f"  ❌ Service Principal incompleto: faltando {', '.join(missing)}")
            return False
        print("  ✅ Service Principal: configured")
    else:
        print(f"  ❌ Auth method not supported: {workspace.auth_method}")
        return False
    print()

    print("[4/4] Workspace Connection")
    try:
        print("  Connecting to workspace...")
        client = _build_client(workspace)

        status = client.workspace.get_status(path="/")
        workspace_id = getattr(status, "workspace_id", None) or getattr(status, "object_id", None)
        if not workspace_id:
            workspace_id = _extract_workspace_id(workspace.host)
        print(f"  ✅ Connected to workspace ID: {workspace_id}")

        list(islice(client.workspace.list(path="/"), 1))
        print("  ✅ Can list workspace objects")
    except Exception as exc:
        print(f"  ❌ Connection failed: {exc}")
        return False

    print()
    print("=" * 70)
    print("✅ ALL CHECKS PASSED - READY TO RUN INVENTORY")
    print("=" * 70)
    print()
    print("Next steps:")
    print("  1. Run: make inventory-validate")
    print("  2. Run: make inventory")
    print()

    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate Lakeventory config.yaml and workspace access")
    parser.add_argument("-w", "--workspace", help="Workspace name to validate from config.yaml")
    args = parser.parse_args()
    success = run_health_check(args.workspace)
    sys.exit(0 if success else 1)
