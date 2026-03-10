"""Configuration manager for multi-workspace support."""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict


@dataclass
class WorkspaceConfig:
    """Configuration for a single Databricks workspace."""
    
    name: str
    host: str
    auth_method: str  # pat, service_principal
    description: str = ""
    
    # Optional workspace-specific output directory (overrides global)
    output_dir: Optional[str] = None
    
    # PAT authentication
    token: Optional[str] = None
    
    # Service Principal authentication
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    tenant_id: Optional[str] = None
    
    def to_env_vars(self) -> Dict[str, str]:
        """Convert workspace config to environment variables."""
        env_vars = {
            "DATABRICKS_HOST": self.host,
        }
        
        if self.auth_method == "pat" and self.token:
            env_vars["DATABRICKS_TOKEN"] = self.token
        elif self.auth_method == "service_principal":
            if self.client_id:
                env_vars["DATABRICKS_CLIENT_ID"] = self.client_id
            if self.client_secret:
                env_vars["DATABRICKS_CLIENT_SECRET"] = self.client_secret
            if self.tenant_id:
                env_vars["ARM_TENANT_ID"] = self.tenant_id
        
        return env_vars


@dataclass
class GlobalConfig:
    """Global configuration settings."""
    
    output_dir: str = "./output"
    output_format: str = "xlsx"  # markdown, json, xlsx, all
    log_level: str = "info"  # error, info, verbose, debug
    batch_size: int = 200
    batch_sleep_ms: int = 50
    include_runs: bool = False
    include_query_history: bool = False
    include_dbfs: bool = False
    backup_workspace: bool = False
    backup_output_dir: str = ""
    enabled_collectors: List[str] = field(default_factory=lambda: [
        "workspace", "jobs", "clusters", "sql", "mlflow", 
        "unity_catalog", "repos", "security", "identities", "serving"
    ])


@dataclass
class LakeventoryConfig:
    """Top-level configuration for Lakeventory."""
    
    version: str = "1.0"
    default_workspace: Optional[str] = None
    workspaces: Dict[str, WorkspaceConfig] = field(default_factory=dict)
    global_config: GlobalConfig = field(default_factory=GlobalConfig)
    
    @classmethod
    def from_yaml(cls, config_path: Path) -> "LakeventoryConfig":
        """Load configuration from YAML file."""
        if not config_path.exists():
            return cls()
        
        with open(config_path, 'r') as f:
            data = yaml.safe_load(f) or {}
        
        # Parse workspaces
        workspaces = {}
        for name, ws_data in data.get("workspaces", {}).items():
            workspaces[name] = WorkspaceConfig(name=name, **ws_data)
        
        # Parse global config
        global_data = data.get("global_config", {})
        global_config = GlobalConfig(**global_data)
        
        return cls(
            version=data.get("version", "1.0"),
            default_workspace=data.get("default_workspace"),
            workspaces=workspaces,
            global_config=global_config,
        )
    
    def to_yaml(self, config_path: Path) -> None:
        """Save configuration to YAML file."""
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to dict, filtering out None values and secrets
        workspaces_dict = {}
        for name, ws in self.workspaces.items():
            ws_dict = asdict(ws)
            # Remove name field (it's the key)
            ws_dict.pop("name", None)
            # Filter None values
            ws_dict = {k: v for k, v in ws_dict.items() if v is not None}
            workspaces_dict[name] = ws_dict
        
        data = {
            "version": self.version,
            "default_workspace": self.default_workspace,
            "workspaces": workspaces_dict,
            "global_config": asdict(self.global_config),
        }
        
        with open(config_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    
    def get_workspace(self, name: Optional[str] = None) -> Optional[WorkspaceConfig]:
        """Get workspace configuration by name or default."""
        if name:
            return self.workspaces.get(name)
        elif self.default_workspace:
            return self.workspaces.get(self.default_workspace)
        elif len(self.workspaces) == 1:
            return list(self.workspaces.values())[0]
        return None
    
    def add_workspace(self, workspace: WorkspaceConfig) -> None:
        """Add or update a workspace configuration."""
        self.workspaces[workspace.name] = workspace
        
        # Set as default if it's the first workspace
        if len(self.workspaces) == 1:
            self.default_workspace = workspace.name
    
    def remove_workspace(self, name: str) -> bool:
        """Remove a workspace configuration."""
        if name in self.workspaces:
            del self.workspaces[name]
            
            # Update default if removed
            if self.default_workspace == name:
                self.default_workspace = list(self.workspaces.keys())[0] if self.workspaces else None
            
            return True
        return False
    
    def list_workspaces(self) -> List[str]:
        """List all workspace names."""
        return list(self.workspaces.keys())


class ConfigManager:
    """Manages Lakeventory configuration files."""
    
    DEFAULT_CONFIG_DIR = Path(".lakeventory")
    DEFAULT_CONFIG_FILE = "config.yaml"
    
    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize config manager."""
        self.config_dir = config_dir or self.DEFAULT_CONFIG_DIR
        self.config_path = self.config_dir / self.DEFAULT_CONFIG_FILE
    
    def load(self) -> LakeventoryConfig:
        """Load configuration from file or create default."""
        if self.config_path.exists():
            return LakeventoryConfig.from_yaml(self.config_path)

        return LakeventoryConfig()
    
    def save(self, config: LakeventoryConfig) -> None:
        """Save configuration to file."""
        config.to_yaml(self.config_path)
    
    def apply_workspace_env(self, workspace: WorkspaceConfig) -> None:
        """Apply workspace configuration to environment variables."""
        env_vars = workspace.to_env_vars()
        for key, value in env_vars.items():
            os.environ[key] = value
