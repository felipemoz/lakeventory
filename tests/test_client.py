from pathlib import Path

import lakeventory.client as client


class FakeWorkspaceClient:
    def __init__(self, **kwargs):
        self.kwargs = kwargs

def test_build_workspace_client_token(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(client, "WorkspaceClient", FakeWorkspaceClient)
    monkeypatch.setenv("DATABRICKS_HOST", "https://example")
    monkeypatch.setenv("DATABRICKS_TOKEN", "abc123")

    wc = client.build_workspace_client(tmp_path)

    assert isinstance(wc, FakeWorkspaceClient)
    assert wc.kwargs["host"] == "https://example"
    assert wc.kwargs["token"] == "abc123"


def test_build_workspace_client_missing_host(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("DATABRICKS_HOST", raising=False)
    monkeypatch.setenv("DATABRICKS_TOKEN", "abc123")

    try:
        client.build_workspace_client(tmp_path)
        assert False, "Expected RuntimeError"
    except RuntimeError as exc:
        assert "DATABRICKS_HOST" in str(exc)

def test_build_workspace_client_service_principal(monkeypatch, tmp_path: Path):
    """Test building WorkspaceClient with Service Principal."""
    monkeypatch.setattr(client, "WorkspaceClient", FakeWorkspaceClient)
    monkeypatch.setenv("DATABRICKS_HOST", "https://example")
    monkeypatch.setenv("DATABRICKS_CLIENT_ID", "abc123")
    monkeypatch.setenv("DATABRICKS_CLIENT_SECRET", "xyz789")
    
    wc = client.build_workspace_client(tmp_path)
    
    assert isinstance(wc, FakeWorkspaceClient)
    assert wc.kwargs["host"] == "https://example"
    assert wc.kwargs["client_id"] == "abc123"
    assert wc.kwargs["client_secret"] == "xyz789"

