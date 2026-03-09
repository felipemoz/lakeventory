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
