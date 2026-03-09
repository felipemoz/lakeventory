"""Data models for inventory."""

from dataclasses import dataclass


@dataclass
class Finding:
    """Represents a discovered asset in the Databricks workspace."""
    path: str
    kind: str
    notes: str
    lockin_count: int = 0
    lockin_details: str = ""
