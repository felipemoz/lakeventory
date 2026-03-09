"""Cloud lock-in pattern analysis for notebook/source content."""

import re
from typing import Dict, List


LOCKIN_PATTERNS = {
    "aws": {
        "s3_path": r"\bs3a?://",
        "boto3": r"\bboto3\b",
        "botocore": r"\bbotocore\b",
        "awswrangler": r"\bawswrangler\b",
        "athena": r"\bathena\b",
        "glue": r"\bglue\b",
        "redshift": r"\bredshift\b",
        "dynamodb": r"\bdynamodb\b",
        "kinesis": r"\bkinesis\b",
        "emr": r"\bemr\b",
    },
    "azure": {
        "abfss_path": r"\babfss?://",
        "wasbs_path": r"\bwasbs?://",
        "adl_path": r"\badl://",
        "adls": r"\badls\b",
        "adf": r"\badf\b|\bazure\s+data\s+factory\b",
        "azure_storage_sdk": r"\bazure\.storage\b",
        "azure_identity_sdk": r"\bazure\.identity\b",
        "azure_keyvault_sdk": r"\bazure\.keyvault\b",
        "synapse": r"\bsynapse\b",
    },
    "gcp": {
        "gcs_path": r"\bgs://",
        "google_cloud_sdk": r"\bgoogle\.cloud\b",
        "bigquery": r"\bbigquery\b",
        "dataproc": r"\bdataproc\b",
        "gcsfs": r"\bgcsfs\b",
    },
}


def analyze_cloud_lockin(text: str) -> Dict:
    """Analyze text for cloud provider lock-in indicators.

    Returns dict with total counts and provider/pattern breakdown.
    """
    if not text:
        return {
            "total": 0,
            "providers": {"aws": 0, "azure": 0, "gcp": 0},
            "by_pattern": {},
        }

    total = 0
    providers = {"aws": 0, "azure": 0, "gcp": 0}
    by_pattern: Dict[str, int] = {}

    for provider, patterns in LOCKIN_PATTERNS.items():
        for pattern_name, pattern_regex in patterns.items():
            count = len(re.findall(pattern_regex, text, flags=re.IGNORECASE))
            if count > 0:
                by_pattern[pattern_name] = count
                providers[provider] += count
                total += count

    return {
        "total": total,
        "providers": providers,
        "by_pattern": by_pattern,
    }


def format_lockin_details(analysis: Dict) -> str:
    """Format lock-in analysis into compact string for inventory columns."""
    if not analysis or analysis.get("total", 0) == 0:
        return ""

    providers = analysis.get("providers", {})
    non_zero_providers: List[str] = [
        f"{name}:{count}"
        for name, count in providers.items()
        if isinstance(count, int) and count > 0
    ]
    return ", ".join(non_zero_providers)
