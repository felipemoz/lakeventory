"""Permissions validator for Databricks workspace inventory."""

from databricks.sdk import WorkspaceClient
from typing import Dict, List, Tuple
import os


class PermissionsValidator:
    """Validate that the current user has required permissions for inventory."""

    def __init__(self, client: WorkspaceClient):
        self.client = client
        self.results = {}
        self.warnings = []

    def validate_all(self, exclude_heavy: bool = True) -> Tuple[bool, Dict[str, bool], List[str]]:
        """
        Validate all permissions.
        
        Returns:
            (all_passed: bool, results: dict of {api_name: bool}, warnings: list of str)
        """
        cloud_provider = os.getenv("DATABRICKS_CLOUD_PROVIDER", "").upper()
        
        # Core APIs (always checked)
        self._check_workspace_api()
        self._check_jobs_api()
        self._check_clusters_api(cloud_provider)
        self._check_sql_api()
        self._check_mlflow_api()
        self._check_unity_catalog_api()
        self._check_repos_api()
        self._check_security_api()
        self._check_identities_api()
        self._check_serving_api()
        self._check_sharing_api()
        
        # Heavy collectors (only if not excluded)
        if not exclude_heavy:
            self._check_dbfs_api()
        
        all_passed = all(self.results.values())
        return all_passed, self.results, self.warnings

    def _check_workspace_api(self):
        """Check workspace.list permission."""
        try:
            list(self.client.workspace.list(path="/"))
            self.results["workspace"] = True
        except Exception as e:
            self.results["workspace"] = False
            self.warnings.append(f"workspace.list: {str(e)}")

    def _check_jobs_api(self):
        """Check jobs.list permission."""
        try:
            list(self.client.jobs.list(limit=1))
            self.results["jobs"] = True
        except Exception as e:
            self.results["jobs"] = False
            self.warnings.append(f"jobs.list: {str(e)}")

    def _check_clusters_api(self, cloud_provider: str):
        """Check clusters.list permission."""
        try:
            list(self.client.clusters.list(limit=1))
            self.results["clusters"] = True
        except Exception as e:
            self.results["clusters"] = False
            self.warnings.append(f"clusters.list: {str(e)}")

    def _check_sql_api(self):
        """Check sql.list permission."""
        try:
            list(self.client.warehouses.list(limit=1))
            self.results["sql"] = True
        except Exception as e:
            self.results["sql"] = False
            self.warnings.append(f"warehouses.list: {str(e)}")

    def _check_mlflow_api(self):
        """Check mlflow.list permission."""
        try:
            list(self.client.experiments.list(limit=1))
            self.results["mlflow"] = True
        except Exception as e:
            self.results["mlflow"] = False
            self.warnings.append(f"experiments.list: {str(e)}")

    def _check_unity_catalog_api(self):
        """Check unity catalog permissions."""
        try:
            list(self.client.catalogs.list(limit=1))
            self.results["unity_catalog"] = True
        except Exception as e:
            self.results["unity_catalog"] = False
            self.warnings.append(f"catalogs.list: {str(e)}")

    def _check_repos_api(self):
        """Check repos.list permission."""
        try:
            list(self.client.repos.list(limit=1))
            self.results["repos"] = True
        except Exception as e:
            self.results["repos"] = False
            self.warnings.append(f"repos.list: {str(e)}")

    def _check_security_api(self):
        """Check secrets.list_scopes permission."""
        try:
            list(self.client.secrets.list_scopes())
            self.results["security"] = True
        except Exception as e:
            self.results["security"] = False
            self.warnings.append(f"secrets.list_scopes: {str(e)}")

    def _check_identities_api(self):
        """Check users.list permission."""
        try:
            list(self.client.users.list(limit=1))
            self.results["identities"] = True
        except Exception as e:
            self.results["identities"] = False
            self.warnings.append(f"users.list: {str(e)}")

    def _check_serving_api(self):
        """Check serving endpoints permission."""
        try:
            list(self.client.serving_endpoints.list())
            self.results["serving"] = True
        except Exception as e:
            self.results["serving"] = False
            self.warnings.append(f"serving_endpoints.list: {str(e)}")

    def _check_sharing_api(self):
        """Check sharing (delta sharing) permission."""
        try:
            list(self.client.shares.list(limit=1))
            self.results["sharing"] = True
        except Exception as e:
            self.results["sharing"] = False
            self.warnings.append(f"shares.list: {str(e)}")

    def _check_dbfs_api(self):
        """Check dbfs.list permission (heavy collector)."""
        try:
            # Try to list root DBFS
            self.client.dbfs.get_status(path="/")
            self.results["dbfs"] = True
        except Exception as e:
            self.results["dbfs"] = False
            self.warnings.append(f"dbfs.get_status: {str(e)}")

    def format_report(self) -> str:
        """Format permission validation report."""
        lines = []
        lines.append("=" * 70)
        lines.append("PERMISSION VALIDATION REPORT")
        lines.append("=" * 70)
        
        if not self.results:
            return "⚠️  No permissions were validated"
        
        passed = sum(1 for v in self.results.values() if v)
        total = len(self.results)
        
        lines.append(f"\n✅ PASSED: {passed}/{total} permission checks\n")
        
        # Core APIs (required)
        core_apis = ["workspace", "jobs", "clusters", "sql", "mlflow", "unity_catalog", 
                     "repos", "security", "identities", "serving", "sharing"]
        
        lines.append("Core APIs (Required):")
        for api in core_apis:
            if api in self.results:
                status = "✅" if self.results[api] else "❌"
                lines.append(f"  {status} {api.replace('_', ' ').title()}")
        
        # Heavy collectors
        if "dbfs" in self.results:
            lines.append("\nOptional Heavy Collectors:")
            status = "✅" if self.results["dbfs"] else "❌"
            lines.append(f"  {status} DBFS")
        
        if self.warnings:
            lines.append("\n" + "-" * 70)
            lines.append("PERMISSION ERRORS:\n")
            for warning in self.warnings:
                lines.append(f"  ⚠️  {warning}")
        
        lines.append("\n" + "=" * 70)
        
        return "\n".join(lines)
