"""Databricks workspace client management."""

import logging
import os
import warnings as py_warnings
from pathlib import Path
from typing import Dict, Tuple

# Suppress urllib3 OpenSSL warnings
py_warnings.filterwarnings('ignore', message='urllib3 v2 only supports OpenSSL 1.1.1+')

from databricks.sdk import WorkspaceClient

logger = logging.getLogger(__name__)


def _load_env(env_path: Path) -> Dict[str, str]:
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


def load_output_dir(root: Path) -> str:
    """Load output directory from environment configuration.
    
    Args:
        root: Root directory containing .env file
        
    Returns:
        Output directory path (defaults to 'output' if not configured)
    """
    env = _load_env(root / ".env")
    out_dir = env.get("OUTPUT_DIR") or os.getenv("OUTPUT_DIR", "")
    return out_dir.strip() if out_dir else "output"


def _detect_auth_method(env: Dict[str, str]) -> Tuple[str, str]:
    """Detect which authentication method is configured.
    
    Args:
        env: Dictionary loaded from .env file
        
    Returns:
        Tuple of (auth_type, description) where auth_type is one of:
        - "service_principal"
        - "token"
        - "basic" (username/password)
        - "none"
    """
    # Check for Service Principal (priority 1)
    client_id = env.get("DATABRICKS_CLIENT_ID") or os.getenv("DATABRICKS_CLIENT_ID", "")
    client_secret = env.get("DATABRICKS_CLIENT_SECRET") or os.getenv("DATABRICKS_CLIENT_SECRET", "")
    if client_id and client_secret:
        return "service_principal", f"Service Principal (Client ID: {client_id[:8]}...)"
    
    # Check for Token (priority 2)
    token = env.get("DATABRICKS_TOKEN") or os.getenv("DATABRICKS_TOKEN", "")
    if token:
        return "token", "PAT Token"
    
    # Check for Basic Auth (priority 3)
    user = env.get("DATABRICKS_USER") or env.get("DATABRICKS_USERNAME") or os.getenv("DATABRICKS_USER", "") or os.getenv("DATABRICKS_USERNAME", "")
    password = env.get("DATABRICKS_PASSWORD") or os.getenv("DATABRICKS_PASSWORD", "")
    if user and password:
        return "basic", f"Basic Auth (User: {user})"
    
    return "none", "No credentials configured"


def build_workspace_client(root: Path) -> WorkspaceClient:
    """Build WorkspaceClient from environment configuration.
    
    Supports three authentication methods (in order of priority):
    1. Service Principal (DATABRICKS_CLIENT_ID + DATABRICKS_CLIENT_SECRET)
    2. Token (DATABRICKS_TOKEN)
    3. Basic Auth (DATABRICKS_USERNAME + DATABRICKS_PASSWORD)
    
    Args:
        root: Root directory containing .env file
        
    Returns:
        Configured WorkspaceClient instance
        
    Raises:
        RuntimeError: If required credentials are missing
    """
    env = _load_env(root / ".env")
    
    # Get host (required for all auth methods)
    host = env.get("DATABRICKS_HOST") or os.getenv("DATABRICKS_HOST", "")
    cloud_provider = env.get("DATABRICKS_CLOUD_PROVIDER") or os.getenv("DATABRICKS_CLOUD_PROVIDER", "")
    
    if not host:
        raise RuntimeError("Missing DATABRICKS_HOST. Set it in .env or environment.")
    
    # Set environment variables from .env if not already set
    if host and not os.getenv("DATABRICKS_HOST"):
        os.environ["DATABRICKS_HOST"] = host
    if cloud_provider and not os.getenv("DATABRICKS_CLOUD_PROVIDER"):
        os.environ["DATABRICKS_CLOUD_PROVIDER"] = cloud_provider
    
    # Detect and get appropriate credentials
    client_id = env.get("DATABRICKS_CLIENT_ID") or os.getenv("DATABRICKS_CLIENT_ID", "")
    client_secret = env.get("DATABRICKS_CLIENT_SECRET") or os.getenv("DATABRICKS_CLIENT_SECRET", "")
    token = env.get("DATABRICKS_TOKEN") or os.getenv("DATABRICKS_TOKEN", "")
    user = env.get("DATABRICKS_USER") or env.get("DATABRICKS_USERNAME") or os.getenv("DATABRICKS_USER", "") or os.getenv("DATABRICKS_USERNAME", "")
    password = env.get("DATABRICKS_PASSWORD") or os.getenv("DATABRICKS_PASSWORD", "")
    
    # Set environment variables for Service Principal if provided
    if client_id and not os.getenv("DATABRICKS_CLIENT_ID"):
        os.environ["DATABRICKS_CLIENT_ID"] = client_id
    if client_secret and not os.getenv("DATABRICKS_CLIENT_SECRET"):
        os.environ["DATABRICKS_CLIENT_SECRET"] = client_secret
    if user and not os.getenv("DATABRICKS_USERNAME"):
        os.environ["DATABRICKS_USERNAME"] = user
    if password and not os.getenv("DATABRICKS_PASSWORD"):
        os.environ["DATABRICKS_PASSWORD"] = password
    if token and not os.getenv("DATABRICKS_TOKEN"):
        os.environ["DATABRICKS_TOKEN"] = token
    
    # Detect authentication method
    auth_type, auth_desc = _detect_auth_method(env)
    logger.info("Detected authentication method: %s", auth_desc)
    
    # Try authentication in order of priority
    # Priority 1: Service Principal
    if client_id and client_secret:
        logger.debug("Authenticating with Service Principal (Client ID: %s...)", client_id[:8])
        return WorkspaceClient(
            host=host,
            client_id=client_id,
            client_secret=client_secret
        )
    
    # Priority 2: Token
    if token:
        logger.debug("Authenticating with PAT Token")
        return WorkspaceClient(host=host, token=token)
    
    # Priority 3: Basic Auth
    if user and password:
        logger.debug("Authenticating with username/password")
        return WorkspaceClient(host=host, username=user, password=password)
    
    # No valid credentials
    raise RuntimeError(
        "Missing Databricks credentials. Configure one of:\n"
        "  1. Service Principal: DATABRICKS_CLIENT_ID + DATABRICKS_CLIENT_SECRET\n"
        "  2. PAT Token: DATABRICKS_TOKEN\n"
        "  3. Basic Auth: DATABRICKS_USERNAME + DATABRICKS_PASSWORD"
    )
