"""Databricks workspace client management."""

import logging
import os
import warnings as py_warnings
from pathlib import Path

# Suppress urllib3 OpenSSL warnings
py_warnings.filterwarnings('ignore', message='urllib3 v2 only supports OpenSSL 1.1.1+')

from databricks.sdk import WorkspaceClient

logger = logging.getLogger(__name__)


def build_workspace_client(root: Path) -> WorkspaceClient:
    """Build WorkspaceClient from environment variables.

    Credentials are expected to be already present in ``os.environ``,
    set by :meth:`ConfigManager.apply_workspace_env` before this call.

    Authentication priority (same as Databricks SDK):
    1. Service Principal (DATABRICKS_CLIENT_ID + DATABRICKS_CLIENT_SECRET)
    2. PAT Token (DATABRICKS_TOKEN)

    Args:
        root: Unused; kept for call-site compatibility.

    Returns:
        Configured WorkspaceClient instance.

    Raises:
        RuntimeError: If DATABRICKS_HOST or credentials are missing.
    """
    host = os.getenv("DATABRICKS_HOST", "").strip()
    if not host:
        raise RuntimeError(
            "DATABRICKS_HOST não configurado.\n"
            "Configure via 'make setup' ou crie .lakeventory/config.yaml"
        )

    client_id = os.getenv("DATABRICKS_CLIENT_ID", "").strip()
    client_secret = os.getenv("DATABRICKS_CLIENT_SECRET", "").strip()
    token = os.getenv("DATABRICKS_TOKEN", "").strip()

    if client_id and client_secret:
        logger.debug("Autenticando com Service Principal (client_id: %s...)", client_id[:8])
        return WorkspaceClient(host=host, client_id=client_id, client_secret=client_secret)

    if token:
        logger.debug("Autenticando com PAT Token")
        return WorkspaceClient(host=host, token=token)

    raise RuntimeError(
        "Credenciais Databricks não configuradas. Use 'make setup' para configurar.\n"
        "Métodos suportados via .lakeventory/config.yaml:\n"
        "  1. Service Principal: client_id + client_secret\n"
        "  2. PAT Token: token"
    )
