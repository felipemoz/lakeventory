"""Tests for delta output formatting."""

import tempfile
from pathlib import Path

import pytest

from lakeventory.models import Finding
from lakeventory.output import write_delta_markdown, write_delta_excel


def test_write_delta_markdown():
    """Test writing delta markdown report."""
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = Path(tmpdir) / "delta.md"
        
        delta_findings = [
            Finding(path="/Users/new", kind="notebook", notes="new notebook"),
            Finding(path="/Users/modified", kind="job", notes="modified job"),
        ]
        
        stats = {
            "added": 1,
            "removed": 1,
            "unchanged": 10,
            "modified": 1,
        }
        
        warnings = ["Warning 1", "Warning 2"]
        
        write_delta_markdown(delta_findings, stats, warnings, out_path)
        
        assert out_path.exists()
        content = out_path.read_text()
        
        assert "Delta Report" in content
        assert "Added" in content and "1" in content
        assert "Removed" in content
        assert "Modified" in content
        assert "Warning 1" in content


def test_write_delta_excel():
    """Test writing delta Excel report."""
    try:
        import openpyxl
    except ImportError:
        pytest.skip("openpyxl not installed")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = Path(tmpdir) / "delta.xlsx"
        
        delta_findings = [
            Finding(path="/Users/new", kind="notebook", notes="new notebook"),
        ]
        
        stats = {
            "added": 1,
            "removed": 0,
            "unchanged": 10,
            "modified": 0,
        }
        
        warnings = []
        
        write_delta_excel(delta_findings, stats, warnings, out_path)
        
        assert out_path.exists()
        
        # Verify structure
        wb = openpyxl.load_workbook(out_path)
        assert "Summary" in wb.sheetnames
        
        summary = wb["Summary"]
        data = list(summary.values)
        assert any("Added" in str(row) for row in data)


def test_delta_no_changes():
    """Test delta report when nothing changed."""
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = Path(tmpdir) / "delta.md"
        
        delta_findings = []
        stats = {
            "added": 0,
            "removed": 0,
            "unchanged": 50,
            "modified": 0,
        }
        
        write_delta_markdown(delta_findings, stats, [], out_path)
        
        content = out_path.read_text()
        assert "No Changes" in content or "identical" in content
