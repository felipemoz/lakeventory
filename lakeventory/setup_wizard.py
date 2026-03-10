"""Interactive setup wizard for Lakeventory multi-workspace configuration."""

import getpass
import re
import sys
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from databricks.sdk import WorkspaceClient

from lakeventory.workspace_config import (
    ConfigManager,
    LakeventoryConfig,
    WorkspaceConfig,
)
from lakeventory.permissions_validator import PermissionsValidator


def print_header(text: str, width: int = 60) -> None:
    """Print formatted header."""
    print(f"\n{'━' * width}")
    print(text)
    print('━' * width)


def print_section(text: str) -> None:
    """Print section header."""
    print(f"\n{text}")
    print('─' * len(text))


def read_secret(prompt: str, _unused_env_key: str = "") -> str:
    """Read secret from prompt, with visible fallback."""
    try:
        value = getpass.getpass(f"{prompt}: ").strip()
    except (EOFError, KeyboardInterrupt, Exception):
        value = ""

    if not value:
        print("  ⚠️  Hidden input failed; switching to visible input.")
        value = input(f"{prompt} (visible input): ").strip()
    return value


def validate_workspace_url(url: str) -> bool:
    """Validate Databricks workspace URL format."""
    if not url:
        return False
    
    # Add https:// if missing
    if not url.startswith(('http://', 'https://')):
        url = f'https://{url}'
    
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname
        
        if not hostname:
            return False
        
        # Check for Databricks patterns
        patterns = [
            r'adb-\d+\.\d+\.azuredatabricks\.net',  # Azure
            r'dbc-[a-z0-9-]+\.(cloud|dev)\.databricks\.com',  # AWS/GCP
            r'.*\.cloud\.databricks\.com',  # Community
        ]
        
        for pattern in patterns:
            if re.match(pattern, hostname):
                return True
        
        print(f"  ⚠️  Warning: URL doesn't match typical Databricks patterns")
        return True  # Allow custom domains
        
    except Exception:
        return False


def _extract_workspace_id(host: str) -> str:
    """Extract workspace identifier from host as a fallback."""
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
    safe = re.sub(r"[^a-zA-Z0-9]+", "-", hostname).strip("-")
    return safe or "workspace"


def test_connection(workspace: WorkspaceConfig) -> Optional[dict]:
    """Test workspace connection and return info if successful."""
    try:
        client = _build_workspace_client(workspace)
        
        # Get workspace info
        status = client.workspace.get_status(path="/")
        workspace_id = getattr(status, "workspace_id", None) or getattr(status, "object_id", None)
        if not workspace_id:
            workspace_id = _extract_workspace_id(workspace.host)
        
        # Try to get current user
        try:
            current_user = client.current_user.me()
            user_name = current_user.user_name
        except:
            user_name = "Unknown"
        
        # Run permissions validation
        validator = PermissionsValidator(client)
        all_passed, results, warnings = validator.validate_all()
        
        collectors_available = sum(1 for passed in results.values() if passed)
        collectors_total = len(results)
        
        return {
            "workspace_id": workspace_id,
            "user_name": user_name,
            "collectors_available": collectors_available,
            "collectors_total": collectors_total,
            "permissions_check": results,
        }
    except Exception as e:
        print(f"  ❌ Connection failed: {str(e)}")
        return None


def add_workspace_wizard(config: LakeventoryConfig) -> Optional[WorkspaceConfig]:
    """Interactive wizard to add a new workspace."""
    print_header("➕ Add New Workspace")
    
    # Workspace name
    while True:
        name = input("\nWorkspace name (e.g., dev/staging/prod): ").strip()
        if not name:
            print("  ❌ Name cannot be empty")
            continue
        if name in config.workspaces:
            print(f"  ⚠️  Workspace '{name}' already exists")
            overwrite = input("  Overwrite? [y/N]: ").strip().lower()
            if overwrite != 'y':
                continue
        break
    
    # Description
    description = input("Description (optional): ").strip()
    
    # Workspace URL
    while True:
        host = input("\n📍 Databricks Workspace URL: ").strip()
        if not host.startswith(('http://', 'https://')):
            host = f'https://{host}'
        
        if validate_workspace_url(host):
            break
        print("  ❌ Invalid URL format")
    
    # Auth method
    print_section("Choose authentication method")
    print("  1. 🔑 Personal Access Token (PAT)")
    print("  2. 🤖 Service Principal (OAuth)")
    
    while True:
        choice = input("\nSelect [1-2]: ").strip()
        if choice in ['1', '2']:
            break
        print("  ❌ Invalid choice")
    
    # Collect auth credentials
    token = None
    client_id = None
    client_secret = None
    tenant_id = None
    
    if choice == '1':
        auth_method = 'pat'
        print_section("🔑 Personal Access Token (PAT)")
        token = read_secret("Enter PAT token")
        if not token:
            print("  ❌ Token cannot be empty")
            return None
    
    elif choice == '2':
        auth_method = 'service_principal'
        print_section("🤖 Service Principal (OAuth)")
        client_id = input("Client ID: ").strip()
        client_secret = read_secret("Client Secret")
        tenant_id = input("Tenant ID (Azure AD): ").strip()
        
        if not client_id or not client_secret or not tenant_id:
            print("  ❌ All fields are required for Service Principal")
            return None
    
    else:
        print("  ❌ Invalid choice")
        return None
    
    # Create workspace config
    workspace = WorkspaceConfig(
        name=name,
        host=host,
        auth_method=auth_method,
        description=description,
        token=token,
        client_id=client_id,
        client_secret=client_secret,
        tenant_id=tenant_id,
    )
    
    # Test connection
    print("\n⏳ Testing connection...")
    conn_info = test_connection(workspace)
    
    if conn_info:
        print(f"  ✅ Connected to workspace ID: {conn_info['workspace_id']}")
        print(f"  ✅ User: {conn_info['user_name']}")
        print(f"  ✅ Permissions: {conn_info['collectors_available']}/{conn_info['collectors_total']} collectors available")
    else:
        retry = input("\nConnection failed. Add anyway? [y/N]: ").strip().lower()
        if retry != 'y':
            return None
    
    # Add to config
    config.add_workspace(workspace)
    print(f"\n✅ Workspace '{name}' added successfully!")
    
    # Set as default
    if not config.default_workspace or len(config.workspaces) == 1:
        config.default_workspace = name
        print(f"  ℹ️  Set as default workspace")
    else:
        set_default = input(f"\nSet '{name}' as default workspace? [y/N]: ").strip().lower()
        if set_default == 'y':
            config.default_workspace = name
    
    return workspace


def list_workspaces(config: LakeventoryConfig) -> None:
    """List all configured workspaces."""
    print_header("📋 Configured Workspaces")
    
    if not config.workspaces:
        print("\nNo workspaces configured yet.")
        return
    
    print(f"\n{'Name':<15} {'Host':<40} {'Auth Method':<20} {'Status'}")
    print('─' * 90)
    
    for name, ws in config.workspaces.items():
        default_marker = " *" if name == config.default_workspace else ""
        host_short = ws.host.replace('https://', '')[:38]
        
        # Quick connection test
        status = "⏳"
        try:
            client = _build_workspace_client(ws)
            client.workspace.get_status(path="/")
            status = "✅"
        except:
            status = "❌"
        
        print(f"{name:<15}{default_marker:<2} {host_short:<38} {ws.auth_method:<18} {status}")
    
    if config.default_workspace:
        print(f"\n* = default workspace")


def remove_workspace_wizard(config: LakeventoryConfig) -> bool:
    """Interactive wizard to remove a workspace."""
    if not config.workspaces:
        print("\n❌ No workspaces to remove")
        return False
    
    print_header("❌ Remove Workspace")
    list_workspaces(config)
    
    name = input("\nWorkspace name to remove: ").strip()
    
    if name not in config.workspaces:
        print(f"  ❌ Workspace '{name}' not found")
        return False
    
    confirm = input(f"  ⚠️  Remove workspace '{name}'? [y/N]: ").strip().lower()
    if confirm != 'y':
        print("  Cancelled")
        return False
    
    config.remove_workspace(name)
    print(f"  ✅ Workspace '{name}' removed")
    return True


def edit_workspace_wizard(config: LakeventoryConfig) -> bool:
    """Interactive wizard to edit an existing workspace."""
    if not config.workspaces:
        print("\n❌ No workspaces to edit")
        return False

    print_header("📝 Edit Workspace")
    print("\nAvailable workspaces:")
    for name in config.workspaces.keys():
        default = " (default)" if name == config.default_workspace else ""
        print(f"  • {name}{default}")

    name = input("\nWorkspace name to edit: ").strip()
    if name not in config.workspaces:
        print(f"  ❌ Workspace '{name}' not found")
        return False

    current = config.workspaces[name]

    print("\nPress Enter to keep current value.")

    while True:
        host_input = input(f"Host [{current.host}]: ").strip()
        host = host_input or current.host
        if not host.startswith(("http://", "https://")):
            host = f"https://{host}"
        if validate_workspace_url(host):
            break
        print("  ❌ Invalid URL format")

    description_input = input(f"Description [{current.description}]: ").strip()
    description = description_input if description_input else current.description

    current_output_dir = current.output_dir or ""
    output_dir_input = input(f"Output dir [{current_output_dir}]: ").strip()
    output_dir = output_dir_input if output_dir_input else current.output_dir

    print_section("Authentication")
    print(f"Current auth method: {current.auth_method}")
    print("  1. 🔑 Personal Access Token (PAT)")
    print("  2. 🤖 Service Principal (OAuth)")
    auth_choice = input("Select [1-2] (Enter to keep current): ").strip()

    if auth_choice == "1":
        auth_method = "pat"
    elif auth_choice == "2":
        auth_method = "service_principal"
    else:
        auth_method = current.auth_method

    token = current.token
    client_id = current.client_id
    client_secret = current.client_secret
    tenant_id = current.tenant_id

    if auth_method == "pat":
        update_token = input("Update PAT token? [y/N]: ").strip().lower()
        if update_token == "y":
            token = read_secret("Enter PAT token")
            if not token:
                print("  ❌ Token cannot be empty")
                return False
        client_id = ""
        client_secret = ""
        tenant_id = ""
    else:
        print("\n🤖 Service Principal settings")
        client_id_input = input(f"Client ID [{current.client_id or ''}]: ").strip()
        client_id = client_id_input if client_id_input else current.client_id

        update_secret = input("Update Client Secret? [y/N]: ").strip().lower()
        if update_secret == "y":
            client_secret = read_secret("Client Secret")

        tenant_input = input(f"Tenant ID [{current.tenant_id or ''}]: ").strip()
        tenant_id = tenant_input if tenant_input else current.tenant_id

        if not client_id or not client_secret or not tenant_id:
            print("  ❌ client_id, client_secret and tenant_id are required for Service Principal")
            return False
        token = ""

    updated = WorkspaceConfig(
        name=name,
        host=host,
        auth_method=auth_method,
        description=description,
        output_dir=output_dir,
        token=token,
        client_id=client_id,
        client_secret=client_secret,
        tenant_id=tenant_id,
    )

    print("\n⏳ Testing updated connection...")
    conn_info = test_connection(updated)
    if conn_info:
        print(f"  ✅ Connected to workspace ID: {conn_info['workspace_id']}")
        print(f"  ✅ User: {conn_info['user_name']}")
    else:
        keep = input("\nConnection failed. Save changes anyway? [y/N]: ").strip().lower()
        if keep != "y":
            print("  Cancelled")
            return False

    config.workspaces[name] = updated
    print(f"\n✅ Workspace '{name}' updated successfully!")
    return True


def _build_workspace_client(workspace: WorkspaceConfig) -> WorkspaceClient:
    """Build a WorkspaceClient from WorkspaceConfig fields."""
    if workspace.auth_method == "service_principal":
        return WorkspaceClient(
            host=workspace.host,
            client_id=workspace.client_id,
            client_secret=workspace.client_secret,
        )
    # Default: PAT
    return WorkspaceClient(host=workspace.host, token=workspace.token)


def configure_backup_settings(config: LakeventoryConfig) -> None:
    """Configure global backup behavior for workspace export."""
    print_header("💾 Backup Settings")
    current_enabled = "enabled" if config.global_config.backup_workspace else "disabled"
    current_dir = config.global_config.backup_output_dir or "(uses output_dir)"
    print(f"\nCurrent backup mode: {current_enabled}")
    print(f"Current backup output dir: {current_dir}")

    enable = input("\nEnable workspace backup before inventory? [y/N]: ").strip().lower()
    config.global_config.backup_workspace = enable == "y"

    if config.global_config.backup_workspace:
        backup_dir = input(
            "Backup output dir (optional, empty = use output_dir): "
        ).strip()
        config.global_config.backup_output_dir = backup_dir
        print("  ✅ Backup settings updated")
    else:
        config.global_config.backup_output_dir = ""
        print("  ✅ Backup disabled")


def main_menu(config: LakeventoryConfig, config_manager: ConfigManager) -> None:
    """Main interactive menu."""
    print_header("🚀 Lakeventory Multi-Workspace Setup")
    
    if config.workspaces:
        print(f"\n📋 Current workspaces: {len(config.workspaces)}")
        for name in config.workspaces.keys():
            default = " (default)" if name == config.default_workspace else ""
            print(f"  • {name}{default}")
    else:
        print("\n📋 No workspaces configured yet")
    
    while True:
        print("\nWhat would you like to do?")
        print("  1. ➕ Add new workspace")
        print("  2. 📝 Edit existing workspace")
        print("  3. ❌ Remove workspace")
        print("  4. 🔍 List all workspaces")
        print("  5. ⚙️  Set default workspace")
        print("  6. 💾 Configure backup settings")
        print("  7. ✅ Save and exit")
        print("  8. 🚪 Exit without saving")
        
        choice = input("\nSelect [1-8]: ").strip()
        
        if choice == '1':
            add_workspace_wizard(config)
        
        elif choice == '2':
            edit_workspace_wizard(config)
        
        elif choice == '3':
            remove_workspace_wizard(config)
        
        elif choice == '4':
            list_workspaces(config)
        
        elif choice == '5':
            if not config.workspaces:
                print("\n❌ No workspaces to set as default")
                continue
            
            print("\nAvailable workspaces:")
            for name in config.workspaces.keys():
                print(f"  • {name}")
            
            name = input("\nDefault workspace: ").strip()
            if name in config.workspaces:
                config.default_workspace = name
                print(f"  ✅ Default workspace set to '{name}'")
            else:
                print(f"  ❌ Workspace '{name}' not found")
        
        elif choice == '6':
            configure_backup_settings(config)

        elif choice == '7':
            config_manager.save(config)
            print(f"\n✅ Configuration saved to {config_manager.config_path}")
            print("\nNext steps:")
            print("  • lakeventory --help")
            print("  • lakeventory --list-workspaces")
            if config.default_workspace:
                print(f"  • lakeventory  # Run on default workspace ({config.default_workspace})")
            if len(config.workspaces) > 1:
                print("  • lakeventory --all-workspaces  # Run on all workspaces")
            if config.global_config.backup_workspace:
                print("  • lakeventory --backup-workspace  # Run backup mode")
            break
        
        elif choice == '8':
            print("\n🚪 Exiting without saving")
            break
        
        else:
            print("  ❌ Invalid choice")


def run_setup_wizard() -> int:
    """Run the interactive setup wizard."""
    config_manager = ConfigManager()
    config = config_manager.load()
    
    try:
        main_menu(config, config_manager)
        return 0
    except KeyboardInterrupt:
        print("\n\n  Cancelled by user")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(run_setup_wizard())
