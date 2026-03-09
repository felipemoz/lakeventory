from databricks_inventory.lockin import analyze_cloud_lockin, format_lockin_details


def test_analyze_cloud_lockin_detects_aws_and_azure():
    text = """
import boto3
spark.read.parquet('s3://my-bucket/path')
df.write.format('delta').save('abfss://container@acc.dfs.core.windows.net/path')
"""
    analysis = analyze_cloud_lockin(text)

    assert analysis["total"] >= 3
    assert analysis["providers"]["aws"] >= 2
    assert analysis["providers"]["azure"] >= 1


def test_format_lockin_details_empty():
    details = format_lockin_details({"total": 0, "providers": {"aws": 0, "azure": 0, "gcp": 0}})
    assert details == ""


def test_format_lockin_details_non_empty():
    details = format_lockin_details({"total": 4, "providers": {"aws": 3, "azure": 1, "gcp": 0}})
    assert "aws:3" in details
    assert "azure:1" in details
