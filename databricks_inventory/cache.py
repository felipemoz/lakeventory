"""Cache management for incremental inventory runs.

Handles storing and comparing inventory snapshots to detect changes.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from .models import Finding


class InventoryCache:
    """Manages inventory snapshots for incremental runs."""

    def __init__(self, cache_dir: Path = None):
        """Initialize cache manager.
        
        Args:
            cache_dir: Directory to store cache files. Defaults to .inventory_cache
        """
        self.cache_dir = cache_dir or Path(".inventory_cache")
        self.cache_dir.mkdir(exist_ok=True, parents=True)

    def get_latest_snapshot(self) -> Optional[Dict]:
        """Load the most recent inventory snapshot.
        
        Returns:
            Dict with findings or None if no cache exists
        """
        snapshot_files = sorted(self.cache_dir.glob("snapshot_*.json"))
        if not snapshot_files:
            return None
        
        latest = snapshot_files[-1]
        with open(latest, "r") as f:
            return json.load(f)

    def save_snapshot(self, findings: List[Finding]) -> Path:
        """Save current findings as a snapshot.
        
        Args:
            findings: List of Finding objects to cache
            
        Returns:
            Path to saved snapshot file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.cache_dir / f"snapshot_{timestamp}.json"
        
        # Convert findings to dicts
        data = {
            "timestamp": timestamp,
            "count": len(findings),
            "findings": [
                {
                    "path": f.path,
                    "kind": f.kind,
                    "notes": f.notes or "",
                    "lockin_count": f.lockin_count,
                    "lockin_details": f.lockin_details or "",
                }
                for f in findings
            ]
        }
        
        with open(filename, "w") as f:
            json.dump(data, f, indent=2)
        
        return filename

    def compute_delta(
        self, current: List[Finding], previous_snapshot: Optional[Dict] = None
    ) -> Tuple[List[Finding], Dict]:
        """Compare current findings with previous snapshot.
        
        Args:
            current: List of current Finding objects
            previous_snapshot: Previous snapshot dict (loaded via get_latest_snapshot)
            
        Returns:
            Tuple of (delta_findings, stats)
            - delta_findings: Only new/changed findings
            - stats: Dict with counts of added/removed/unchanged
        """
        if not previous_snapshot:
            return current, {
                "added": len(current),
                "removed": 0,
                "unchanged": 0,
                "modified": 0,
            }
        
        # Build key sets for comparison
        current_key_to_finding = {
            (f.path, f.kind): f for f in current
        }
        
        previous_keys = {
            (f["path"], f["kind"]): f
            for f in previous_snapshot.get("findings", [])
        }
        
        # Calculate deltas
        added = []
        modified = []
        unchanged = []
        
        for key, finding in current_key_to_finding.items():
            if key not in previous_keys:
                added.append(finding)
            elif (
                previous_keys[key].get("notes") != finding.notes
                or previous_keys[key].get("lockin_count", 0) != finding.lockin_count
                or previous_keys[key].get("lockin_details", "") != finding.lockin_details
            ):
                modified.append(finding)
            else:
                unchanged.append(finding)
        
        removed_count = len(previous_keys) - len(unchanged) - len(modified)
        
        stats = {
            "added": len(added),
            "removed": removed_count,
            "unchanged": len(unchanged),
            "modified": len(modified),
        }
        
        # Delta findings = added + modified (changed items)
        delta_findings = added + modified
        
        return delta_findings, stats

    def get_cache_info(self) -> Dict:
        """Get information about cached snapshots.
        
        Returns:
            Dict with cache statistics
        """
        snapshot_files = sorted(self.cache_dir.glob("snapshot_*.json"))
        
        snapshots = []
        for f in snapshot_files:
            try:
                with open(f, "r") as fp:
                    data = json.load(fp)
                    snapshots.append({
                        "file": f.name,
                        "timestamp": data.get("timestamp"),
                        "count": data.get("count"),
                    })
            except Exception:
                pass
        
        return {
            "cache_dir": str(self.cache_dir),
            "total_snapshots": len(snapshots),
            "snapshots": snapshots,
        }

    def clear_cache(self) -> int:
        """Delete all cache files.
        
        Returns:
            Number of files deleted
        """
        files = list(self.cache_dir.glob("snapshot_*.json"))
        for f in files:
            f.unlink()
        return len(files)
