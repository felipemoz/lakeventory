"""Databricks workspace client management."""

import os
import warnings as py_warnings
from pathlib import Path
from typing import Dict

# Suppress urllib3 OpenSSL warnings
py_warnings.filterwarnings('ignore', message='urllib3 v2 only supports OpenSSL 1.1.1+')

from databricks.sdk import WorkspaceClient


def load_env(env_path: Path) -> Dict[str, str]:
    """Load environment variables from .env file.
    
    Args:
        env_path: Path to .env file
        
    Returns:
        Dictionary of environment variables
    """
    if not env_path.exists():
        return {}
    env: Dict[str, str] = {}
    for line in env_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        env[key.strip()] = value.strip().strip("'\"")
    return env


def build_workspace_client(root: Path) -> WorkspaceClient:
    """Build WorkspaceClient from environment configuration.
    
    Args:
        root: Root directory containing .env file
        
    Returns:
        Configured WorkspaceClient instance
        
    Raises:
        RuntimeError: If required credentials are missing
    """
    env = load_env(root / ".env")
    host = env.get("DATABRICKS_HOST") or os.getenv("DATABRICKS_HOST", "")
    user = env.get("DATABRICKS_USER") or env.get("DATABRICKS_USERNAME") or os.getenv("DATABRICKS_USER", "")
    password = env.get("DATABRICKS_PASSWORD") or os.getenv("DATABRICKS_PASSWORD", "")
    token = env.get("DATABRICKS_TOKEN") or os.getenv("DATABRICKS_TOKEN", "")
    cloud_provider = env.get("DATABRICKS_CLOUD_PROVIDER") or os.getenv("DATABRICKS_CLOUD_PROVIDER", "")

    if host and not os.getenv("DATABRICKS_HOST"):
        os.environ["DATABRICKS_HOST"] = host
    if user and not os.getenv("DATABRICKS_USERNAME"):
        os.environ["DATABRICKS_USERNAME"] = user
    if password and not os.getenv("DATABRICKS_PASSWORD"):
        os.environ["DATABRICKS_PASSWORD"] = password
    if token and not os.getenv("DATABRICKS_TOKEN"):
        os.environ["DATABRICKS_TOKEN"] = token
    if cloud_provider and not os.getenv("DATABRICKS_CLOUD_PROVIDER"):
        os.environ["DATABRICKS_CLOUD_PROVIDER"] = cloud_provider

    if not host:
        raise RuntimeError("Missing DATABRICKS_HOST. Set it in .env or environment.")

    if host and (user and password):
        return WorkspaceClient(host=host, username=user, password=password)
    if host and token:
        return WorkspaceClient(host=host, token=token)
    raise RuntimeError(
        "Missing Databricks credentials. Set DATABRICKS_USERNAME and DATABRICKS_PASSWORD or DATABRICKS_TOKEN."
    )
