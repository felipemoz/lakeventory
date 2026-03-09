import os
from pathlib import Path

import databricks_inventory.client as client


class FakeWorkspaceClient:
    def __init__(self, **kwargs):
        self.kwargs = kwargs


def test_load_env(tmp_path: Path):
    env_path = tmp_path / ".env"
    env_path.write_text("""
# comment
DATABRICKS_HOST=https://example
DATABRICKS_TOKEN=abc123
EMPTY=
""".strip())

    data = client.load_env(env_path)

    assert data["DATABRICKS_HOST"] == "https://example"
    assert data["DATABRICKS_TOKEN"] == "abc123"
    assert "EMPTY" in data


def test_build_workspace_client_token(monkeypatch, tmp_path: Path):
    env_path = tmp_path / ".env"
    env_path.write_text("""
DATABRICKS_HOST=https://example
DATABRICKS_TOKEN=abc123
""".strip())

    monkeypatch.setattr(client, "WorkspaceClient", FakeWorkspaceClient)
    monkeypatch.delenv("DATABRICKS_HOST", raising=False)
    monkeypatch.delenv("DATABRICKS_TOKEN", raising=False)

    wc = client.build_workspace_client(tmp_path)

    assert isinstance(wc, FakeWorkspaceClient)
    assert wc.kwargs["host"] == "https://example"
    assert wc.kwargs["token"] == "abc123"


def test_build_workspace_client_user_pass(monkeypatch, tmp_path: Path):
    env_path = tmp_path / ".env"
    env_path.write_text("""
DATABRICKS_HOST=https://example
DATABRICKS_USERNAME=user
DATABRICKS_PASSWORD=pass
""".strip())

    monkeypatch.setattr(client, "WorkspaceClient", FakeWorkspaceClient)
    monkeypatch.delenv("DATABRICKS_HOST", raising=False)
    monkeypatch.delenv("DATABRICKS_USERNAME", raising=False)
    monkeypatch.delenv("DATABRICKS_PASSWORD", raising=False)
    monkeypatch.delenv("DATABRICKS_TOKEN", raising=False)

    wc = client.build_workspace_client(tmp_path)

    assert isinstance(wc, FakeWorkspaceClient)
    assert wc.kwargs["host"] == "https://example"
    assert wc.kwargs["username"] == "user"
    assert wc.kwargs["password"] == "pass"


def test_build_workspace_client_missing_host(tmp_path: Path, monkeypatch):
    env_path = tmp_path / ".env"
    env_path.write_text("DATABRICKS_TOKEN=abc123")

    monkeypatch.delenv("DATABRICKS_HOST", raising=False)
    monkeypatch.delenv("DATABRICKS_USERNAME", raising=False)
    monkeypatch.delenv("DATABRICKS_PASSWORD", raising=False)
    monkeypatch.delenv("DATABRICKS_TOKEN", raising=False)

    try:
        client.build_workspace_client(tmp_path)
        assert False, "Expected RuntimeError"
    except RuntimeError as exc:
        assert "Missing DATABRICKS_HOST" in str(exc)


def test_load_output_dir_from_env(tmp_path: Path, monkeypatch):
    env_path = tmp_path / ".env"
    env_path.write_text("OUTPUT_DIR=/custom/output")
    
    monkeypatch.delenv("OUTPUT_DIR", raising=False)
    
    result = client.load_output_dir(tmp_path)
    
    assert result == "/custom/output"


def test_load_output_dir_from_os_env(tmp_path: Path, monkeypatch):
    env_path = tmp_path / ".env"
    env_path.write_text("")
    
    monkeypatch.setenv("OUTPUT_DIR", "/os/output")
    
    result = client.load_output_dir(tmp_path)
    
    assert result == "/os/output"


def test_load_output_dir_defaults_to_output(tmp_path: Path, monkeypatch):
    env_path = tmp_path / ".env"
    env_path.write_text("")
    
    monkeypatch.delenv("OUTPUT_DIR", raising=False)
    
    result = client.load_output_dir(tmp_path)
    
    assert result == "output"


def test_load_output_dir_priority(tmp_path: Path, monkeypatch):
    """Test that .env OUTPUT_DIR takes priority over OS env."""
    env_path = tmp_path / ".env"
    env_path.write_text("OUTPUT_DIR=/env/output")
    
    monkeypatch.setenv("OUTPUT_DIR", "/os/output")
    
    result = client.load_output_dir(tmp_path)
    
    assert result == "/env/output"


def test_detect_auth_method_service_principal(tmp_path: Path, monkeypatch):
    """Test detection of Service Principal authentication."""
    env_path = tmp_path / ".env"
    env_path.write_text("""
DATABRICKS_HOST=https://example
DATABRICKS_CLIENT_ID=abc123
DATABRICKS_CLIENT_SECRET=xyz789
""".strip())
    
    monkeypatch.delenv("DATABRICKS_CLIENT_ID", raising=False)
    monkeypatch.delenv("DATABRICKS_CLIENT_SECRET", raising=False)
    
    env = client.load_env(env_path)
    auth_type, description = client.detect_auth_method(env)
    
    assert auth_type == "service_principal"
    assert "Service Principal" in description
    assert "abc123" in description


def test_detect_auth_method_token(tmp_path: Path, monkeypatch):
    """Test detection of Token authentication."""
    env_path = tmp_path / ".env"
    env_path.write_text("""
DATABRICKS_HOST=https://example
DATABRICKS_TOKEN=dapi1234567890
""".strip())
    
    monkeypatch.delenv("DATABRICKS_TOKEN", raising=False)
    
    env = client.load_env(env_path)
    auth_type, description = client.detect_auth_method(env)
    
    assert auth_type == "token"
    assert "PAT Token" in description


def test_detect_auth_method_basic(tmp_path: Path, monkeypatch):
    """Test detection of Basic Auth (username/password)."""
    env_path = tmp_path / ".env"
    env_path.write_text("""
DATABRICKS_HOST=https://example
DATABRICKS_USERNAME=user
DATABRICKS_PASSWORD=pass
""".strip())
    
    monkeypatch.delenv("DATABRICKS_USERNAME", raising=False)
    monkeypatch.delenv("DATABRICKS_PASSWORD", raising=False)
    monkeypatch.delenv("DATABRICKS_TOKEN", raising=False)
    monkeypatch.delenv("DATABRICKS_CLIENT_ID", raising=False)
    monkeypatch.delenv("DATABRICKS_CLIENT_SECRET", raising=False)
    
    env = client.load_env(env_path)
    auth_type, description = client.detect_auth_method(env)
    
    assert auth_type == "basic"
    assert "Basic Auth" in description
    assert "user" in description


def test_detect_auth_method_none(tmp_path: Path, monkeypatch):
    """Test detection when no authentication is configured."""
    env_path = tmp_path / ".env"
    env_path.write_text("DATABRICKS_HOST=https://example")
    
    monkeypatch.delenv("DATABRICKS_CLIENT_ID", raising=False)
    monkeypatch.delenv("DATABRICKS_CLIENT_SECRET", raising=False)
    monkeypatch.delenv("DATABRICKS_TOKEN", raising=False)
    monkeypatch.delenv("DATABRICKS_USERNAME", raising=False)
    monkeypatch.delenv("DATABRICKS_PASSWORD", raising=False)
    
    env = client.load_env(env_path)
    auth_type, description = client.detect_auth_method(env)
    
    assert auth_type == "none"


def test_detect_auth_priority_service_principal_over_token(tmp_path: Path, monkeypatch):
    """Test that Service Principal takes priority over Token."""
    env_path = tmp_path / ".env"
    env_path.write_text("""
DATABRICKS_CLIENT_ID=abc123
DATABRICKS_CLIENT_SECRET=xyz789
DATABRICKS_TOKEN=dapi1234567890
DATABRICKS_USERNAME=user
DATABRICKS_PASSWORD=pass
""".strip())
    
    monkeypatch.delenv("DATABRICKS_CLIENT_ID", raising=False)
    monkeypatch.delenv("DATABRICKS_CLIENT_SECRET", raising=False)
    monkeypatch.delenv("DATABRICKS_TOKEN", raising=False)
    monkeypatch.delenv("DATABRICKS_USERNAME", raising=False)
    monkeypatch.delenv("DATABRICKS_PASSWORD", raising=False)
    
    env = client.load_env(env_path)
    auth_type, _ = client.detect_auth_method(env)
    
    # Should detect Service Principal (priority 1)
    assert auth_type == "service_principal"


def test_build_workspace_client_service_principal(monkeypatch, tmp_path: Path):
    """Test building WorkspaceClient with Service Principal."""
    env_path = tmp_path / ".env"
    env_path.write_text("""
DATABRICKS_HOST=https://example
DATABRICKS_CLIENT_ID=abc123
DATABRICKS_CLIENT_SECRET=xyz789
""".strip())
    
    monkeypatch.setattr(client, "WorkspaceClient", FakeWorkspaceClient)
    monkeypatch.delenv("DATABRICKS_HOST", raising=False)
    monkeypatch.delenv("DATABRICKS_CLIENT_ID", raising=False)
    monkeypatch.delenv("DATABRICKS_CLIENT_SECRET", raising=False)
    
    wc = client.build_workspace_client(tmp_path)
    
    assert isinstance(wc, FakeWorkspaceClient)
    assert wc.kwargs["host"] == "https://example"
    assert wc.kwargs["client_id"] == "abc123"
    assert wc.kwargs["client_secret"] == "xyz789"

