"""Databricks workspace client management."""

import logging
import warnings as py_warnings
from pathlib import Path
from typing import Optional

# Suppress urllib3 OpenSSL warnings
py_warnings.filterwarnings('ignore', message='urllib3 v2 only supports OpenSSL 1.1.1+')

from databricks.sdk import WorkspaceClient
from lakeventory.workspace_config import ConfigManager

logger = logging.getLogger(__name__)


def build_workspace_client(root: Path, http_timeout_seconds: Optional[int] = None) -> WorkspaceClient:
    """Build WorkspaceClient from environment variables.

    Credentials are expected to be already present in ``os.environ``,
    set by :meth:`ConfigManager.apply_workspace_env` before this call.

    Authentication priority (same as Databricks SDK):
    1. Service Principal (DATABRICKS_CLIENT_ID + DATABRICKS_CLIENT_SECRET)
    2. PAT Token (DATABRICKS_TOKEN)

    Args:
        root: Unused; kept for call-site compatibility.
        http_timeout_seconds: Per-request HTTP timeout in seconds passed
            through from ``global_config.http_timeout_seconds`` in
            ``.lakeventory/config.yaml`` (or the ``--http-timeout`` CLI flag).
            ``None`` (the default) lets the Databricks SDK choose.  Increase
            this for large workspaces where collector calls (e.g.
            ``tables.list()``, ``users.list()``) can legitimately take several
            minutes.

    Returns:
        Configured WorkspaceClient instance.

    Raises:
        RuntimeError: If DATABRICKS_HOST or credentials are missing.
    """
    config = ConfigManager().load()
    workspace = config.get_workspace(config.default_workspace)
    if not workspace:
        raise RuntimeError(
            "No workspace configured in config.yaml.\n"
            "Configure via 'make setup' or set default_workspace."
        )

    return build_workspace_client_with_config(
        root,
        host=workspace.host,
        token=workspace.token,
        client_id=workspace.client_id,
        client_secret=workspace.client_secret,
        timeout_seconds=getattr(config.global_config, "timeout", None),
    )


def build_workspace_client_with_config(
    root: Path,
    *,
    host: Optional[str] = None,
    token: Optional[str] = None,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
    timeout_seconds: Optional[int] = None,
) -> WorkspaceClient:
    """Build WorkspaceClient from explicit config values (YAML-first)."""
    resolved_host = (host or "").strip()
    if not resolved_host:
        raise RuntimeError(
            "DATABRICKS_HOST not configured.\n"
            "Configure via 'make setup' or create .lakeventory/config.yaml"
        )

    resolved_client_id = (client_id or "").strip()
    resolved_client_secret = (client_secret or "").strip()
    resolved_token = (token or "").strip()

    def _create_client(**kwargs):
        if timeout_seconds and timeout_seconds > 0:
            try:
                return WorkspaceClient(http_timeout_seconds=timeout_seconds, **kwargs)
            except TypeError:
                logger.debug("WorkspaceClient does not accept http_timeout_seconds; using SDK default timeout")
        return WorkspaceClient(**kwargs)

    if resolved_client_id and resolved_client_secret:
        logger.debug("Authenticating with Service Principal (client_id: %s...)", resolved_client_id[:8])
        return _create_client(
            host=resolved_host,
            client_id=resolved_client_id,
            client_secret=resolved_client_secret,
        )

    if resolved_token:
        logger.debug("Authenticating with PAT Token")
        return _create_client(host=resolved_host, token=resolved_token)

    raise RuntimeError(
        "Databricks credentials not configured. Use 'make setup' to configure.\n"
        "Supported methods via .lakeventory/config.yaml:\n"
        "  1. Service Principal: client_id + client_secret\n"
        "  2. PAT Token: token"
    )
    if client_id and client_secret:
        logger.debug("Autenticando com Service Principal (client_id: %s...)", client_id[:8])
        config = DatabricksConfig(
            host=host,
            client_id=client_id,
            client_secret=client_secret,
            http_timeout_seconds=http_timeout_seconds,
        )
    elif token:
        logger.debug("Autenticando com PAT Token")
        config = DatabricksConfig(
            host=host,
            token=token,
            http_timeout_seconds=http_timeout_seconds,
        )
    else:
        raise RuntimeError(
            "Credenciais Databricks não configuradas. Use 'make setup' para configurar.\n"
            "Métodos suportados via .lakeventory/config.yaml:\n"
            "  1. Service Principal: client_id + client_secret\n"
            "  2. PAT Token: token"
        )

    return WorkspaceClient(config=config)
