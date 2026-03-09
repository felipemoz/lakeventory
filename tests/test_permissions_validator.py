"""Tests for permissions validator."""

from unittest.mock import MagicMock, patch
import pytest

from databricks_inventory.permissions_validator import PermissionsValidator


@pytest.fixture
def mock_client():
    """Create a mock Databricks workspace client."""
    return MagicMock()


def test_permissions_validator_all_passed(mock_client):
    """Test when all permissions checks pass."""
    # Mock all API calls to succeed
    mock_client.workspace.list.return_value = []
    mock_client.jobs.list.return_value = []
    mock_client.clusters.list.return_value = []
    mock_client.warehouses.list.return_value = []
    mock_client.experiments.list.return_value = []
    mock_client.catalogs.list.return_value = []
    mock_client.repos.list.return_value = []
    mock_client.secrets.list_scopes.return_value = []
    mock_client.users.list.return_value = []
    mock_client.serving_endpoints.list.return_value = []
    mock_client.shares.list.return_value = []
    
    validator = PermissionsValidator(mock_client)
    all_passed, results, warnings = validator.validate_all(exclude_heavy=True)
    
    assert all_passed is True
    assert len(warnings) == 0
    assert all(results.values())


def test_permissions_validator_some_failures(mock_client):
    """Test when some permission checks fail."""
    # Mock some API calls to succeed, others to fail
    mock_client.workspace.list.return_value = []
    mock_client.jobs.list.side_effect = Exception("Permission denied")
    mock_client.clusters.list.return_value = []
    mock_client.warehouses.list.return_value = []
    mock_client.experiments.list.return_value = []
    mock_client.catalogs.list.return_value = []
    mock_client.repos.list.return_value = []
    mock_client.secrets.list_scopes.return_value = []
    mock_client.users.list.return_value = []
    mock_client.serving_endpoints.list.return_value = []
    mock_client.shares.list.return_value = []
    
    validator = PermissionsValidator(mock_client)
    all_passed, results, warnings = validator.validate_all(exclude_heavy=True)
    
    assert all_passed is False
    assert results["jobs"] is False
    assert results["workspace"] is True
    assert len(warnings) > 0


def test_permissions_validator_format_report(mock_client):
    """Test that the permission report is formatted correctly."""
    mock_client.workspace.list.return_value = []
    mock_client.jobs.list.return_value = []
    mock_client.clusters.list.side_effect = Exception("Forbidden")
    mock_client.warehouses.list.return_value = []
    mock_client.experiments.list.return_value = []
    mock_client.catalogs.list.return_value = []
    mock_client.repos.list.return_value = []
    mock_client.secrets.list_scopes.return_value = []
    mock_client.users.list.return_value = []
    mock_client.serving_endpoints.list.return_value = []
    mock_client.shares.list.return_value = []
    
    validator = PermissionsValidator(mock_client)
    all_passed, results, warnings = validator.validate_all(exclude_heavy=True)
    report = validator.format_report()
    
    assert "PERMISSION VALIDATION REPORT" in report
    assert "clusters" in report.lower()
    assert "❌" in report  # Failed check indicator


def test_permissions_validator_excludes_dbfs_by_default(mock_client):
    """Test that DBFS is excluded from validation by default."""
    mock_client.workspace.list.return_value = []
    mock_client.jobs.list.return_value = []
    mock_client.clusters.list.return_value = []
    mock_client.warehouses.list.return_value = []
    mock_client.experiments.list.return_value = []
    mock_client.catalogs.list.return_value = []
    mock_client.repos.list.return_value = []
    mock_client.secrets.list_scopes.return_value = []
    mock_client.users.list.return_value = []
    mock_client.serving_endpoints.list.return_value = []
    mock_client.shares.list.return_value = []
    
    validator = PermissionsValidator(mock_client)
    all_passed, results, warnings = validator.validate_all(exclude_heavy=True)
    
    assert "dbfs" not in results


def test_permissions_validator_includes_dbfs_when_specified(mock_client):
    """Test that DBFS is checked when exclude_heavy=False."""
    mock_client.workspace.list.return_value = []
    mock_client.jobs.list.return_value = []
    mock_client.clusters.list.return_value = []
    mock_client.warehouses.list.return_value = []
    mock_client.experiments.list.return_value = []
    mock_client.catalogs.list.return_value = []
    mock_client.repos.list.return_value = []
    mock_client.secrets.list_scopes.return_value = []
    mock_client.users.list.return_value = []
    mock_client.serving_endpoints.list.return_value = []
    mock_client.shares.list.return_value = []
    mock_client.dbfs.get_status.return_value = MagicMock()
    
    validator = PermissionsValidator(mock_client)
    all_passed, results, warnings = validator.validate_all(exclude_heavy=False)
    
    assert "dbfs" in results
