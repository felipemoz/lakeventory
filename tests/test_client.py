from pathlib import Path

import lakeventory.client as client_module
from lakeventory.client import build_workspace_client


class FakeConfig:
    """Minimal stand-in for DatabricksConfig that records its constructor kwargs."""
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        # Expose attributes the WorkspaceClient constructor may access
        self.host = kwargs.get("host", "")
        self.http_timeout_seconds = kwargs.get("http_timeout_seconds")


class FakeWorkspaceClient:
    """Stand-in for WorkspaceClient that records the config it received."""
    def __init__(self, *, config=None, **kwargs):
        self.config = config
        self.kwargs = kwargs


def test_build_workspace_client_token(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(client_module, "WorkspaceClient", FakeWorkspaceClient)
    monkeypatch.setattr(client_module, "DatabricksConfig", FakeConfig)
    monkeypatch.setenv("DATABRICKS_HOST", "https://example")
    monkeypatch.setenv("DATABRICKS_TOKEN", "abc123")
    monkeypatch.delenv("DATABRICKS_CLIENT_ID", raising=False)
    monkeypatch.delenv("DATABRICKS_CLIENT_SECRET", raising=False)

    wc = build_workspace_client(tmp_path)

    assert isinstance(wc, FakeWorkspaceClient)
    assert wc.config.kwargs["host"] == "https://example"
    assert wc.config.kwargs["token"] == "abc123"


def test_build_workspace_client_missing_host(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("DATABRICKS_HOST", raising=False)
    monkeypatch.setenv("DATABRICKS_TOKEN", "abc123")

    try:
        build_workspace_client(tmp_path)
        assert False, "Expected RuntimeError"
    except RuntimeError as exc:
        assert "DATABRICKS_HOST" in str(exc)


def test_build_workspace_client_service_principal(monkeypatch, tmp_path: Path):
    """Test building WorkspaceClient with Service Principal."""
    monkeypatch.setattr(client_module, "WorkspaceClient", FakeWorkspaceClient)
    monkeypatch.setattr(client_module, "DatabricksConfig", FakeConfig)
    monkeypatch.setenv("DATABRICKS_HOST", "https://example")
    monkeypatch.setenv("DATABRICKS_CLIENT_ID", "abc123")
    monkeypatch.setenv("DATABRICKS_CLIENT_SECRET", "xyz789")
    monkeypatch.delenv("DATABRICKS_TOKEN", raising=False)

    wc = build_workspace_client(tmp_path)

    assert isinstance(wc, FakeWorkspaceClient)
    assert wc.config.kwargs["host"] == "https://example"
    assert wc.config.kwargs["client_id"] == "abc123"
    assert wc.config.kwargs["client_secret"] == "xyz789"


def test_build_workspace_client_explicit_timeout(monkeypatch, tmp_path: Path):
    """Explicit http_timeout_seconds is forwarded to DatabricksConfig."""
    monkeypatch.setattr(client_module, "WorkspaceClient", FakeWorkspaceClient)
    monkeypatch.setattr(client_module, "DatabricksConfig", FakeConfig)
    monkeypatch.setenv("DATABRICKS_HOST", "https://example")
    monkeypatch.setenv("DATABRICKS_TOKEN", "tok")
    monkeypatch.delenv("DATABRICKS_CLIENT_ID", raising=False)
    monkeypatch.delenv("DATABRICKS_CLIENT_SECRET", raising=False)

    wc = build_workspace_client(tmp_path, http_timeout_seconds=600)

    assert wc.config.kwargs["http_timeout_seconds"] == 600


def test_build_workspace_client_no_timeout_by_default(monkeypatch, tmp_path: Path):
    """Without an explicit timeout, http_timeout_seconds is None (SDK default)."""
    monkeypatch.setattr(client_module, "WorkspaceClient", FakeWorkspaceClient)
    monkeypatch.setattr(client_module, "DatabricksConfig", FakeConfig)
    monkeypatch.setenv("DATABRICKS_HOST", "https://example")
    monkeypatch.setenv("DATABRICKS_TOKEN", "tok")
    monkeypatch.delenv("DATABRICKS_CLIENT_ID", raising=False)
    monkeypatch.delenv("DATABRICKS_CLIENT_SECRET", raising=False)

    wc = build_workspace_client(tmp_path)

    assert wc.config.kwargs["http_timeout_seconds"] is None

