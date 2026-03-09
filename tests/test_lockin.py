from databricks_inventory.lockin import analyze_cloud_lockin


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

