"""Tests for cache module."""

import json
import tempfile
import time
from pathlib import Path

import pytest

from databricks_inventory.cache import InventoryCache
from databricks_inventory.models import Finding


def test_cache_save_snapshot():
    """Test saving a snapshot."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = InventoryCache(Path(tmpdir))
        findings = [
            Finding(path="/Users/test", kind="notebook", notes="test nb"),
            Finding(path="/Shared/data", kind="directory", notes=""),
        ]
        
        filename = cache.save_snapshot(findings)
        
        assert filename.exists()
        assert filename.name.startswith("snapshot_")
        
        # Verify content
        with open(filename, "r") as f:
            data = json.load(f)
            assert data["count"] == 2
            assert len(data["findings"]) == 2
            assert data["findings"][0]["path"] == "/Users/test"


def test_cache_load_latest_snapshot():
    """Test loading the latest snapshot."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = InventoryCache(Path(tmpdir))
        
        # No snapshot yet
        assert cache.get_latest_snapshot() is None
        
        # Save first snapshot
        findings1 = [Finding(path="/Users/test", kind="notebook", notes="v1")]
        cache.save_snapshot(findings1)
        
        # Load it
        snapshot = cache.get_latest_snapshot()
        assert snapshot is not None
        assert snapshot["count"] == 1


def test_cache_compute_delta():
    """Test delta computation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = InventoryCache(Path(tmpdir))
        
        # First run - save snapshot
        findings1 = [
            Finding(path="/Users/a", kind="notebook", notes="a"),
            Finding(path="/Users/b", kind="notebook", notes="b"),
            Finding(path="/Users/c", kind="directory", notes="c"),
        ]
        snapshot1 = cache.save_snapshot(findings1)
        
        # Second run - some changes
        findings2 = [
            Finding(path="/Users/a", kind="notebook", notes="a"),  # unchanged
            Finding(path="/Users/b", kind="notebook", notes="b_modified"),  # modified
            Finding(path="/Users/d", kind="notebook", notes="d"),  # new
            # /Users/c deleted
        ]
        
        # Load previous snapshot
        with open(snapshot1, "r") as f:
            prev = json.load(f)
        
        delta, stats = cache.compute_delta(findings2, prev)
        
        assert stats["added"] == 1  # /Users/d
        assert stats["removed"] == 1  # /Users/c
        assert stats["unchanged"] == 1  # /Users/a
        assert stats["modified"] == 1  # /Users/b
        
        # Delta should contain only changed items
        assert len(delta) == 2  # added + modified


def test_cache_info():
    """Test cache info retrieval."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = InventoryCache(Path(tmpdir))
        
        # Empty cache
        info = cache.get_cache_info()
        assert info["total_snapshots"] == 0
        
        # Save some snapshots
        findings = [Finding(path="/Users/test", kind="notebook", notes="")]
        cache.save_snapshot(findings)
        time.sleep(1.1)  # Ensure timestamp is different
        cache.save_snapshot(findings)
        
        # Check info
        info = cache.get_cache_info()
        assert info["total_snapshots"] == 2
        assert len(info["snapshots"]) == 2


def test_cache_clear():
    """Test clearing cache."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = InventoryCache(Path(tmpdir))
        
        # Save some snapshots
        findings = [Finding(path="/Users/test", kind="notebook", notes="")]
        cache.save_snapshot(findings)
        time.sleep(1.1)  # Ensure timestamp is different
        cache.save_snapshot(findings)
        
        # Clear
        deleted = cache.clear_cache()
        assert deleted == 2
        
        # Verify empty
        info = cache.get_cache_info()
        assert info["total_snapshots"] == 0


def test_delta_no_previous():
    """Test delta when no previous snapshot exists."""
    cache = InventoryCache(Path("/tmp/nonexistent_test"))
    
    findings = [
        Finding(path="/Users/a", kind="notebook", notes="a"),
        Finding(path="/Users/b", kind="notebook", notes="b"),
    ]
    
    delta, stats = cache.compute_delta(findings, previous_snapshot=None)
    
    assert len(delta) == 2  # All considered "added" when no previous
    assert stats["added"] == 2
    assert stats["removed"] == 0
    assert stats["unchanged"] == 0
