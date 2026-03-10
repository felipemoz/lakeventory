"""Tests for setup wizard utility functions."""

import concurrent.futures
import time
import pytest
from unittest.mock import Mock, patch, call

from lakeventory.setup_wizard import (
    validate_workspace_url,
    _extract_workspace_id,
    _build_workspace_client,
    edit_workspace_wizard,
    _CONNECTION_TIMEOUT_SECONDS,
    _HTTP_TIMEOUT_SECONDS,
)
from lakeventory.workspace_config import WorkspaceConfig


class TestValidateWorkspaceUrl:
    """Tests for workspace URL validation."""
    
    def test_valid_azure_url(self):
        """Test valid Azure Databricks URL."""
        assert validate_workspace_url("https://adb-123456.13.azuredatabricks.net")
        assert validate_workspace_url("https://adb-7405613732159224.4.azuredatabricks.net")
    
    def test_valid_azure_url_without_https(self):
        """Test Azure URL without https:// prefix."""
        assert validate_workspace_url("adb-123456.13.azuredatabricks.net")
    
    def test_valid_aws_url(self):
        """Test valid AWS Databricks URL."""
        assert validate_workspace_url("https://dbc-abc123-def456.cloud.databricks.com")
        assert validate_workspace_url("dbc-test-workspace.cloud.databricks.com")
    
    def test_valid_gcp_url(self):
        """Test valid GCP Databricks URL."""
        assert validate_workspace_url("https://example-gcp.dev.databricks.com")
    
    def test_valid_community_url(self):
        """Test valid Community Edition URL."""
        assert validate_workspace_url("https://community.cloud.databricks.com")
    
    def test_custom_domain(self):
        """Test custom domain (should pass with warning)."""
        # Custom domains should be allowed
        assert validate_workspace_url("https://databricks.company.com")
    
    def test_empty_url(self):
        """Test empty URL."""
        assert not validate_workspace_url("")
        assert not validate_workspace_url(None)
    
    def test_invalid_url_format(self):
        """Test invalid URL format."""
        # validate_workspace_url returns True with warning for custom domains
        # Only empty/None returns False
        assert validate_workspace_url("not-a-url")  # Returns True with warning
        # FTP URLs have hostname, so they pass with warning
        result = validate_workspace_url("ftp://wrong-protocol.com")
        assert result  # Returns True (hostname exists)


class TestExtractWorkspaceId:
    """Tests for workspace ID extraction from host URL."""
    
    def test_extract_from_azure_url(self):
        """Test extraction from Azure Databricks URL."""
        workspace_id = _extract_workspace_id("https://adb-123456789.13.azuredatabricks.net")
        # Function returns only the numeric ID without 'adb-' prefix
        assert workspace_id == "123456789"
    
    def test_extract_from_aws_url(self):
        """Test extraction from AWS Databricks URL."""
        workspace_id = _extract_workspace_id("https://dbc-abc123-def456.cloud.databricks.com")
        # Function returns only the ID without 'dbc-' prefix
        assert workspace_id == "abc123-def456"
    
    def test_extract_from_url_without_pattern(self):
        """Test extraction from URL without known pattern."""
        workspace_id = _extract_workspace_id("https://custom.company.com")
        # Function converts dots to dashes for safe identifiers
        assert workspace_id == "custom-company-com"
    
    def test_extract_from_empty_host(self):
        """Test extraction with empty host."""
        workspace_id = _extract_workspace_id("")
        assert workspace_id == "workspace"
    
    def test_extract_from_none(self):
        """Test extraction with None."""
        workspace_id = _extract_workspace_id(None)
        assert workspace_id == "workspace"


class TestBuildWorkspaceClient:
    """Tests for workspace client builder."""
    
    @patch('lakeventory.setup_wizard.WorkspaceClient')
    @patch('lakeventory.setup_wizard.DatabricksConfig')
    def test_build_client_with_pat(self, mock_config_cls, mock_client):
        """Test building client with PAT authentication."""
        workspace = WorkspaceConfig(
            name="test",
            host="https://test.databricks.com",
            auth_method="pat",
            token="test-token"
        )
        
        _build_workspace_client(workspace)
        
        mock_config_cls.assert_called_once_with(
            host="https://test.databricks.com",
            token="test-token",
            http_timeout_seconds=_HTTP_TIMEOUT_SECONDS,
        )
        mock_client.assert_called_once_with(config=mock_config_cls.return_value)
    
    @patch('lakeventory.setup_wizard.WorkspaceClient')
    @patch('lakeventory.setup_wizard.DatabricksConfig')
    def test_build_client_with_service_principal(self, mock_config_cls, mock_client):
        """Test building client with Service Principal authentication."""
        workspace = WorkspaceConfig(
            name="test",
            host="https://test.databricks.com",
            auth_method="service_principal",
            client_id="client-123",
            client_secret="secret-456",
            tenant_id="tenant-789"
        )
        
        _build_workspace_client(workspace)
        
        mock_config_cls.assert_called_once_with(
            host="https://test.databricks.com",
            client_id="client-123",
            client_secret="secret-456",
            http_timeout_seconds=_HTTP_TIMEOUT_SECONDS,
        )
        mock_client.assert_called_once_with(config=mock_config_cls.return_value)
    
    @patch('lakeventory.setup_wizard.WorkspaceClient')
    @patch('lakeventory.setup_wizard.DatabricksConfig')
    def test_build_client_defaults_to_pat(self, mock_config_cls, mock_client):
        """Test that unknown auth method defaults to PAT."""
        workspace = WorkspaceConfig(
            name="test",
            host="https://test.databricks.com",
            auth_method="unknown",
            token="test-token"
        )
        
        _build_workspace_client(workspace)
        
        # Should default to PAT behavior
        mock_config_cls.assert_called_once_with(
            host="https://test.databricks.com",
            token="test-token",
            http_timeout_seconds=_HTTP_TIMEOUT_SECONDS,
        )
        mock_client.assert_called_once_with(config=mock_config_cls.return_value)
    
    def test_build_client_sets_http_timeout(self):
        """Test that the built client has the expected HTTP timeout."""
        workspace = WorkspaceConfig(
            name="test",
            host="https://test.databricks.com",
            auth_method="pat",
            token="test-token"
        )
        
        client = _build_workspace_client(workspace)
        
        assert client.config.http_timeout_seconds == _HTTP_TIMEOUT_SECONDS


class TestReadSecret:
    """Tests for read_secret function."""

    @patch.dict('os.environ', {'DATABRICKS_TOKEN': 'env-token'})
    @patch('lakeventory.setup_wizard.getpass.getpass', return_value='typed-secret')
    def test_read_from_env_var(self, mock_getpass):
        """Environment variables are ignored; secret is read via prompt."""
        from lakeventory.setup_wizard import read_secret

        result = read_secret("Enter token", "DATABRICKS_TOKEN")

        assert result == "typed-secret"
        mock_getpass.assert_called_once_with("Enter token: ")
    
    @patch.dict('os.environ', {}, clear=True)
    @patch('lakeventory.setup_wizard.getpass.getpass', return_value='typed-secret')
    def test_read_via_getpass(self, mock_getpass):
        """Test reading secret via getpass when no env var."""
        from lakeventory.setup_wizard import read_secret
        
        result = read_secret("Enter token", "DATABRICKS_TOKEN")
        
        assert result == "typed-secret"
        mock_getpass.assert_called_once_with("Enter token: ")
    
    @patch.dict('os.environ', {}, clear=True)
    @patch('lakeventory.setup_wizard.getpass.getpass', side_effect=KeyboardInterrupt())
    @patch('lakeventory.setup_wizard.input', return_value='visible-input')
    def test_fallback_to_visible_input(self, mock_input, mock_getpass):
        """Test fallback to visible input when getpass fails."""
        from lakeventory.setup_wizard import read_secret
        
        result = read_secret("Enter token", "DATABRICKS_TOKEN")
        
        assert result == "visible-input"
        mock_getpass.assert_called_once()
        mock_input.assert_called_once()


class TestPrintFunctions:
    """Tests for print/display utility functions."""
    
    def test_print_header(self, capsys):
        """Test print_header output."""
        from lakeventory.setup_wizard import print_header
        
        print_header("Test Header")
        captured = capsys.readouterr()
        
        assert "Test Header" in captured.out
        # Uses unicode box drawing character
        assert "━" in captured.out
    
    def test_print_section(self, capsys):
        """Test print_section output."""
        from lakeventory.setup_wizard import print_section
        
        print_section("Test Section")
        captured = capsys.readouterr()
        
        assert "Test Section" in captured.out
        # Uses unicode box drawing character
        assert "─" in captured.out


class TestConnectionTest:
    """Tests for connection testing (mocked)."""
    
    @patch('lakeventory.setup_wizard._build_workspace_client')
    def test_connection_test_success(self, mock_build_client):
        """Test successful connection test."""
        from lakeventory.setup_wizard import test_connection
        
        # Mock workspace client
        mock_client = Mock()
        mock_status = Mock()
        mock_status.workspace_id = "123456"
        mock_client.workspace.get_status.return_value = mock_status
        
        mock_user = Mock()
        mock_user.user_name = "test@example.com"
        mock_client.current_user.me.return_value = mock_user
        
        # Mock collectors check
        mock_client.jobs.list.return_value = []
        mock_client.clusters.list.return_value = []
        
        mock_build_client.return_value = mock_client
        
        workspace = WorkspaceConfig(
            name="test",
            host="https://test.databricks.com",
            auth_method="pat",
            token="token"
        )
        
        result = test_connection(workspace)
        
        assert result is not None
        assert result['workspace_id'] == "123456"
        assert result['user_name'] == "test@example.com"
    
    @patch('lakeventory.setup_wizard._build_workspace_client')
    def test_connection_test_failure(self, mock_build_client):
        """Test connection test with failure."""
        from lakeventory.setup_wizard import test_connection
        
        # Mock client that raises exception
        mock_build_client.side_effect = Exception("Connection failed")
        
        workspace = WorkspaceConfig(
            name="test",
            host="https://test.databricks.com",
            auth_method="pat",
            token="bad-token"
        )
        
        result = test_connection(workspace)
        
        assert result is None

    @patch('lakeventory.setup_wizard._build_workspace_client')
    def test_connection_test_timeout(self, mock_build_client, capsys):
        """Test that connection test returns None and prints error when timed out."""
        from lakeventory.setup_wizard import test_connection

        # Simulate a slow connection that exceeds the timeout
        def _slow_connect(workspace):
            time.sleep(60)  # much longer than any timeout

        mock_build_client.side_effect = _slow_connect

        workspace = WorkspaceConfig(
            name="test",
            host="https://invalid-host.example.com",
            auth_method="pat",
            token="dummy-token",
        )

        # Patch the timeout constant to a very short value so the test runs fast
        with patch('lakeventory.setup_wizard._CONNECTION_TIMEOUT_SECONDS', 1):
            result = test_connection(workspace)

        assert result is None
        captured = capsys.readouterr()
        assert "timed out" in captured.out.lower()


class TestIntegrationScenarios:
    """Integration tests for common workflows."""
    
    def test_add_workspace_workflow(self, tmp_path, monkeypatch):
        """Test complete workflow of adding a workspace."""
        from lakeventory.workspace_config import ConfigManager, LakeventoryConfig, WorkspaceConfig
        
        monkeypatch.chdir(tmp_path)
        
        # Initialize manager
        manager = ConfigManager()
        config = LakeventoryConfig()
        
        # Add first workspace
        ws1 = WorkspaceConfig(
            name="prod",
            host="https://prod.databricks.com",
            auth_method="pat",
            token="prod-token",
            description="Production"
        )
        config.add_workspace(ws1)
        config.default_workspace = "prod"
        
        # Save
        manager.save(config)
        
        # Load and verify
        loaded = manager.load()
        assert loaded.default_workspace == "prod"
        assert "prod" in loaded.workspaces
        
        # Add second workspace
        ws2 = WorkspaceConfig(
            name="dev",
            host="https://dev.databricks.com",
            auth_method="pat",
            token="dev-token",
            description="Development"
        )
        loaded.add_workspace(ws2)
        
        # Save again
        manager.save(loaded)
        
        # Reload and verify both workspaces
        final = manager.load()
        assert len(final.workspaces) == 2
        assert "prod" in final.workspaces
        assert "dev" in final.workspaces
        assert final.default_workspace == "prod"
    
    def test_remove_workspace_workflow(self, tmp_path, monkeypatch):
        """Test complete workflow of removing a workspace."""
        from lakeventory.workspace_config import ConfigManager, LakeventoryConfig, WorkspaceConfig
        
        monkeypatch.chdir(tmp_path)
        
        # Setup with multiple workspaces
        manager = ConfigManager()
        config = LakeventoryConfig()
        
        for name in ["prod", "staging", "dev"]:
            ws = WorkspaceConfig(
                name=name,
                host=f"https://{name}.databricks.com",
                auth_method="pat",
                token=f"{name}-token"
            )
            config.add_workspace(ws)
        
        config.default_workspace = "prod"
        manager.save(config)
        
        # Remove one workspace
        loaded = manager.load()
        loaded.remove_workspace("staging")
        manager.save(loaded)
        
        # Verify removal
        final = manager.load()
        assert len(final.workspaces) == 2
        assert "prod" in final.workspaces
        assert "dev" in final.workspaces
        assert "staging" not in final.workspaces
        assert final.default_workspace == "prod"


class TestEditWorkspaceWizard:
    """Tests for edit workspace flow."""

    @patch("lakeventory.setup_wizard.test_connection", return_value={"workspace_id": "1", "user_name": "u"})
    def test_edit_workspace_keep_and_update_fields(self, _mock_conn):
        from lakeventory.workspace_config import LakeventoryConfig, WorkspaceConfig

        config = LakeventoryConfig(
            default_workspace="dev",
            workspaces={
                "dev": WorkspaceConfig(
                    name="dev",
                    host="https://old-host",
                    auth_method="pat",
                    token="old-token",
                    description="old desc",
                )
            },
        )

        inputs = iter(
            [
                "dev",                # workspace name
                "https://new-host",   # host
                "new desc",           # description
                "./new-out",          # output dir
                "",                   # keep auth method
                "n",                  # do not update token
            ]
        )

        with patch("lakeventory.setup_wizard.input", side_effect=lambda *_: next(inputs)):
            ok = edit_workspace_wizard(config)

        assert ok is True
        ws = config.workspaces["dev"]
        assert ws.host == "https://new-host"
        assert ws.description == "new desc"
        assert ws.output_dir == "./new-out"
        assert ws.token == "old-token"

    def test_edit_workspace_not_found(self):
        from lakeventory.workspace_config import LakeventoryConfig, WorkspaceConfig

        config = LakeventoryConfig(
            default_workspace="dev",
            workspaces={
                "dev": WorkspaceConfig(
                    name="dev",
                    host="https://host",
                    auth_method="pat",
                    token="token",
                )
            },
        )

        with patch("lakeventory.setup_wizard.input", return_value="prod"):
            ok = edit_workspace_wizard(config)

        assert ok is False
