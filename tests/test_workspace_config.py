"""Tests for multi-workspace configuration management."""

import os
import yaml
from pathlib import Path
import pytest

from lakeventory.workspace_config import (
    WorkspaceConfig,
    GlobalConfig,
    LakeventoryConfig,
    ConfigManager,
)


class TestWorkspaceConfig:
    """Tests for WorkspaceConfig dataclass."""
    
    def test_pat_workspace_creation(self):
        """Test creating a PAT workspace config."""
        ws = WorkspaceConfig(
            name="prod",
            host="https://adb-123456.13.azuredatabricks.net",
            auth_method="pat",
            token="dapi123",
            description="Production workspace"
        )
        
        assert ws.name == "prod"
        assert ws.host == "https://adb-123456.13.azuredatabricks.net"
        assert ws.auth_method == "pat"
        assert ws.token == "dapi123"
        assert ws.description == "Production workspace"
        assert ws.output_dir is None
    
    def test_service_principal_workspace_creation(self):
        """Test creating a Service Principal workspace config."""
        ws = WorkspaceConfig(
            name="staging",
            host="https://adb-789012.13.azuredatabricks.net",
            auth_method="service_principal",
            client_id="client-id-123",
            client_secret="secret-456",
            tenant_id="tenant-789",
            description="Staging workspace"
        )
        
        assert ws.name == "staging"
        assert ws.auth_method == "service_principal"
        assert ws.client_id == "client-id-123"
        assert ws.client_secret == "secret-456"
        assert ws.tenant_id == "tenant-789"
    
    def test_workspace_with_custom_output_dir(self):
        """Test workspace with custom output directory."""
        ws = WorkspaceConfig(
            name="dev",
            host="https://example.cloud.databricks.com",
            auth_method="pat",
            token="token123",
            output_dir="/custom/path"
        )
        
        assert ws.output_dir == "/custom/path"
    
    def test_to_env_vars_pat(self):
        """Test conversion to environment variables for PAT."""
        ws = WorkspaceConfig(
            name="test",
            host="https://example.com",
            auth_method="pat",
            token="my-token"
        )
        
        env_vars = ws.to_env_vars()
        
        assert env_vars["DATABRICKS_HOST"] == "https://example.com"
        assert env_vars["DATABRICKS_TOKEN"] == "my-token"
        assert "DATABRICKS_CLIENT_ID" not in env_vars
    
    def test_to_env_vars_service_principal(self):
        """Test conversion to environment variables for Service Principal."""
        ws = WorkspaceConfig(
            name="test",
            host="https://example.com",
            auth_method="service_principal",
            client_id="client-123",
            client_secret="secret-456",
            tenant_id="tenant-789"
        )
        
        env_vars = ws.to_env_vars()
        
        assert env_vars["DATABRICKS_HOST"] == "https://example.com"
        assert env_vars["DATABRICKS_CLIENT_ID"] == "client-123"
        assert env_vars["DATABRICKS_CLIENT_SECRET"] == "secret-456"
        assert env_vars["ARM_TENANT_ID"] == "tenant-789"
        assert "DATABRICKS_TOKEN" not in env_vars


class TestGlobalConfig:
    """Tests for GlobalConfig dataclass."""
    
    def test_default_values(self):
        """Test default global config values."""
        config = GlobalConfig()
        
        assert config.output_dir == "./output"
        assert config.output_format == "xlsx"
        assert config.log_level == "info"
        assert config.batch_size == 200
        assert config.batch_sleep_ms == 50
        assert config.include_runs is False
        assert config.include_query_history is False
        assert config.include_dbfs is False
        assert config.backup_workspace is False
        assert config.backup_output_dir == ""
        assert len(config.enabled_collectors) > 0
    
    def test_custom_values(self):
        """Test custom global config values."""
        config = GlobalConfig(
            output_dir="/custom/output",
            output_format="markdown",
            log_level="debug",
            batch_size=100,
            include_runs=True,
            backup_workspace=True,
            backup_output_dir="/tmp/backups",
        )
        
        assert config.output_dir == "/custom/output"
        assert config.output_format == "markdown"
        assert config.log_level == "debug"
        assert config.batch_size == 100
        assert config.backup_workspace is True
        assert config.backup_output_dir == "/tmp/backups"
        assert config.include_runs is True


class TestLakeventoryConfig:
    """Tests for LakeventoryConfig dataclass."""
    
    def test_empty_config(self):
        """Test empty configuration."""
        config = LakeventoryConfig()
        
        assert config.version == "1.0"
        assert config.default_workspace is None
        assert len(config.workspaces) == 0
        assert isinstance(config.global_config, GlobalConfig)
    
    def test_config_with_workspaces(self):
        """Test configuration with multiple workspaces."""
        ws1 = WorkspaceConfig(
            name="prod",
            host="https://prod.databricks.com",
            auth_method="pat",
            token="token1"
        )
        ws2 = WorkspaceConfig(
            name="dev",
            host="https://dev.databricks.com",
            auth_method="pat",
            token="token2"
        )
        
        config = LakeventoryConfig(
            default_workspace="prod",
            workspaces={"prod": ws1, "dev": ws2}
        )
        
        assert config.default_workspace == "prod"
        assert len(config.workspaces) == 2
        assert "prod" in config.workspaces
        assert "dev" in config.workspaces
    
    def test_yaml_serialization(self, tmp_path: Path):
        """Test YAML serialization and deserialization."""
        # Create config
        ws = WorkspaceConfig(
            name="test",
            host="https://test.databricks.com",
            auth_method="pat",
            token="test-token",
            description="Test workspace"
        )
        
        config = LakeventoryConfig(
            default_workspace="test",
            workspaces={"test": ws}
        )
        
        # Save to YAML
        config_path = tmp_path / "config.yaml"
        config.to_yaml(config_path)
        
        assert config_path.exists()
        
        # Load from YAML
        loaded_config = LakeventoryConfig.from_yaml(config_path)
        
        assert loaded_config.version == "1.0"
        assert loaded_config.default_workspace == "test"
        assert "test" in loaded_config.workspaces
        assert loaded_config.workspaces["test"].host == "https://test.databricks.com"
        assert loaded_config.workspaces["test"].token == "test-token"

    def test_yaml_serialization_includes_optional_workspace_keys(self, tmp_path: Path):
        """Optional workspace keys should be explicitly present in YAML output."""
        ws = WorkspaceConfig(
            name="test",
            host="https://test.databricks.com",
            auth_method="pat",
            token="test-token",
        )
        config = LakeventoryConfig(default_workspace="test", workspaces={"test": ws})

        config_path = tmp_path / "config.yaml"
        config.to_yaml(config_path)

        raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        ws_raw = raw["workspaces"]["test"]

        for key in [
            "host",
            "auth_method",
            "description",
            "output_dir",
            "token",
            "client_id",
            "client_secret",
            "tenant_id",
        ]:
            assert key in ws_raw

        assert ws_raw["output_dir"] == ""
        assert ws_raw["client_id"] == ""
        assert ws_raw["client_secret"] == ""
        assert ws_raw["tenant_id"] == ""
    
    def test_get_workspace(self):
        """Test getting workspace by name."""
        ws = WorkspaceConfig(
            name="prod",
            host="https://prod.databricks.com",
            auth_method="pat",
            token="token"
        )
        
        config = LakeventoryConfig(workspaces={"prod": ws})
        
        retrieved = config.get_workspace("prod")
        assert retrieved is not None
        assert retrieved.name == "prod"
        
        not_found = config.get_workspace("nonexistent")
        assert not_found is None
    
    def test_add_workspace(self):
        """Test adding a workspace."""
        config = LakeventoryConfig()
        
        ws = WorkspaceConfig(
            name="new",
            host="https://new.databricks.com",
            auth_method="pat",
            token="token"
        )
        
        config.add_workspace(ws)
        
        assert "new" in config.workspaces
        assert config.workspaces["new"].host == "https://new.databricks.com"
    
    def test_remove_workspace(self):
        """Test removing a workspace."""
        ws = WorkspaceConfig(
            name="temp",
            host="https://temp.databricks.com",
            auth_method="pat",
            token="token"
        )
        
        config = LakeventoryConfig(workspaces={"temp": ws})
        
        assert "temp" in config.workspaces
        
        config.remove_workspace("temp")
        
        assert "temp" not in config.workspaces


class TestConfigManager:
    """Tests for ConfigManager class."""
    
    def test_config_dir_creation(self, tmp_path: Path, monkeypatch):
        """Test that config directory is created on save."""
        monkeypatch.chdir(tmp_path)
        
        manager = ConfigManager()
        config = manager.load()
        
        # Directory is created when save() is called (via to_yaml())
        assert not manager.config_dir.exists()  # Not created yet
        
        manager.save(config)
        
        assert manager.config_dir.exists()  # Now it exists
        assert manager.config_dir.is_dir()
    
    def test_load_creates_default_config(self, tmp_path: Path, monkeypatch):
        """Test loading creates default config when none exists."""
        monkeypatch.chdir(tmp_path)
        
        manager = ConfigManager()
        config = manager.load()
        
        assert isinstance(config, LakeventoryConfig)
        assert config.version == "1.0"
        assert len(config.workspaces) == 0
    
    def test_save_and_load(self, tmp_path: Path, monkeypatch):
        """Test saving and loading configuration."""
        monkeypatch.chdir(tmp_path)
        
        manager = ConfigManager()
        
        # Create config
        ws = WorkspaceConfig(
            name="test",
            host="https://test.databricks.com",
            auth_method="pat",
            token="test-token"
        )
        
        config = LakeventoryConfig(
            default_workspace="test",
            workspaces={"test": ws}
        )
        
        # Save
        manager.save(config)
        
        # Load
        loaded = manager.load()
        
        assert loaded.default_workspace == "test"
        assert "test" in loaded.workspaces
        assert loaded.workspaces["test"].token == "test-token"
    
    def test_load_ignores_env_without_config(self, tmp_path: Path, monkeypatch):
        """Sem config.yaml, não migra automaticamente de .env."""
        monkeypatch.chdir(tmp_path)

        env_path = tmp_path / ".env"
        env_path.write_text("""
DATABRICKS_HOST=https://migrated.databricks.com
DATABRICKS_TOKEN=migrated-token
""".strip())

        manager = ConfigManager()
        config = manager.load()

        assert len(config.workspaces) == 0
        assert config.default_workspace is None
    
    def test_apply_workspace_env(self, tmp_path: Path, monkeypatch):
        """Test applying workspace environment variables."""
        monkeypatch.chdir(tmp_path)
        
        ws = WorkspaceConfig(
            name="test",
            host="https://test.databricks.com",
            auth_method="pat",
            token="applied-token"
        )
        
        manager = ConfigManager()
        manager.apply_workspace_env(ws)
        
        # Check environment variables were set
        assert os.environ.get("DATABRICKS_HOST") == "https://test.databricks.com"
        assert os.environ.get("DATABRICKS_TOKEN") == "applied-token"
    
    def test_existing_config_is_loaded_even_with_env_file(self, tmp_path: Path, monkeypatch):
        """Com config.yaml existente, o load preserva config e ignora .env."""
        monkeypatch.chdir(tmp_path)
        
        # Create existing config
        manager = ConfigManager()
        existing_ws = WorkspaceConfig(
            name="existing",
            host="https://existing.databricks.com",
            auth_method="pat",
            token="existing-token"
        )
        existing_config = LakeventoryConfig(
            default_workspace="existing",
            workspaces={"existing": existing_ws}
        )
        manager.save(existing_config)
        
        # Create .env file (should be ignored)
        env_path = tmp_path / ".env"
        env_path.write_text("""
DATABRICKS_HOST=https://should-be-ignored.databricks.com
DATABRICKS_TOKEN=ignored-token
""".strip())
        
        # Load config
        loaded = manager.load()
        
        # Should have existing config, not migrated
        assert loaded.default_workspace == "existing"
        assert "default" not in loaded.workspaces
        assert loaded.workspaces["existing"].host == "https://existing.databricks.com"


class TestYAMLSerialization:
    """Tests for YAML serialization edge cases."""
    
    def test_empty_optional_fields(self, tmp_path: Path):
        """Test serialization with empty optional fields."""
        ws = WorkspaceConfig(
            name="minimal",
            host="https://minimal.databricks.com",
            auth_method="pat",
            token="token"
        )
        
        config = LakeventoryConfig(workspaces={"minimal": ws})
        
        config_path = tmp_path / "config.yaml"
        config.to_yaml(config_path)
        
        # Check YAML doesn't have null values for optional fields
        with open(config_path) as f:
            yaml_content = f.read()
        
        # Should have the workspace
        assert "minimal" in yaml_content
        assert "https://minimal.databricks.com" in yaml_content
    
    def test_multiple_workspaces_serialization(self, tmp_path: Path):
        """Test serialization with multiple workspaces."""
        ws1 = WorkspaceConfig(
            name="prod",
            host="https://prod.databricks.com",
            auth_method="service_principal",
            client_id="prod-client",
            client_secret="prod-secret",
            tenant_id="prod-tenant"
        )
        
        ws2 = WorkspaceConfig(
            name="dev",
            host="https://dev.databricks.com",
            auth_method="pat",
            token="dev-token",
            output_dir="/tmp/dev-output"
        )
        
        config = LakeventoryConfig(
            default_workspace="prod",
            workspaces={"prod": ws1, "dev": ws2}
        )
        
        config_path = tmp_path / "config.yaml"
        config.to_yaml(config_path)
        
        # Load and verify
        loaded = LakeventoryConfig.from_yaml(config_path)
        
        assert loaded.default_workspace == "prod"
        assert len(loaded.workspaces) == 2
        
        # Check prod workspace
        prod = loaded.workspaces["prod"]
        assert prod.auth_method == "service_principal"
        assert prod.client_id == "prod-client"
        
        # Check dev workspace
        dev = loaded.workspaces["dev"]
        assert dev.auth_method == "pat"
        assert dev.token == "dev-token"
        assert dev.output_dir == "/tmp/dev-output"
