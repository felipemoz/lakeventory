from pathlib import Path

import lakeventory.client as client


class FakeWorkspaceClient:
    def __init__(self, **kwargs):
        self.kwargs = kwargs

def test_build_workspace_client_token(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(client, "WorkspaceClient", FakeWorkspaceClient)
    wc = client.build_workspace_client_with_config(
        tmp_path,
        host="https://example",
        token="abc123",
    )

    assert isinstance(wc, FakeWorkspaceClient)
    assert wc.kwargs["host"] == "https://example"
    assert wc.kwargs["token"] == "abc123"


def test_build_workspace_client_missing_host(tmp_path: Path, monkeypatch):
    try:
        client.build_workspace_client_with_config(tmp_path, token="abc123")
        assert False, "Expected RuntimeError"
    except RuntimeError as exc:
        assert "DATABRICKS_HOST" in str(exc)

def test_build_workspace_client_service_principal(monkeypatch, tmp_path: Path):
    """Test building WorkspaceClient with Service Principal."""
    monkeypatch.setattr(client, "WorkspaceClient", FakeWorkspaceClient)
    wc = client.build_workspace_client_with_config(
        tmp_path,
        host="https://example",
        client_id="abc123",
        client_secret="xyz789",
    )
    
    assert isinstance(wc, FakeWorkspaceClient)
    assert wc.kwargs["host"] == "https://example"
    assert wc.kwargs["client_id"] == "abc123"
    assert wc.kwargs["client_secret"] == "xyz789"


def test_build_workspace_client_with_config_explicit_pat(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(client, "WorkspaceClient", FakeWorkspaceClient)
    monkeypatch.delenv("DATABRICKS_HOST", raising=False)
    monkeypatch.delenv("DATABRICKS_TOKEN", raising=False)

    wc = client.build_workspace_client_with_config(
        tmp_path,
        host="https://explicit-host",
        token="explicit-token",
        timeout_seconds=123,
    )

    assert isinstance(wc, FakeWorkspaceClient)
    assert wc.kwargs["host"] == "https://explicit-host"
    assert wc.kwargs["token"] == "explicit-token"
    assert wc.kwargs["http_timeout_seconds"] == 123

