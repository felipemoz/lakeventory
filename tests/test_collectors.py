import os
import base64

from databricks_inventory.collectors import (
    collect_workspace_objects,
    collect_jobs,
    collect_clusters,
    collect_findings_selective,
)
from databricks_inventory.models import Finding


class Obj:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class Service:
    def __init__(self, items=None, list_fn_name="list"):
        self._items = items or []
        self._list_fn_name = list_fn_name

    def list(self, *args, **kwargs):
        return self._items

    def list_runs(self, *args, **kwargs):
        return self._items


class PipelinesService:
    def __init__(self, items=None):
        self._items = items or []

    def list_pipelines(self, *args, **kwargs):
        return self._items


class WorkspaceService:
    def __init__(self, by_path):
        self._by_path = by_path

    def list(self, path="/"):
        return self._by_path.get(path, [])

    def export(self, path="/", format="SOURCE"):
        source = self._by_path.get("__source__", {}).get(path, "")
        encoded = base64.b64encode(source.encode("utf-8")).decode("utf-8")
        return Obj(content=encoded)


class FakeClient:
    def __init__(self, workspace_by_path):
        self.workspace = WorkspaceService(workspace_by_path)
        self.jobs = Service([])
        self.clusters = Service([])
        self.cluster_policies = Service([])
        self.global_init_scripts = Service([])
        self.instance_profiles = Service([])
        self.instance_pools = Service([])


def test_collect_workspace_objects():
    ws = {
        "/": [Obj(object_type="DIRECTORY", path="/dir"), Obj(object_type="NOTEBOOK", path="/nb", language="PY")],
        "/dir": [],
        "__source__": {
            "/nb": "import boto3\ndf = spark.read.parquet('s3://bucket/path')",
        },
    }
    client = FakeClient(ws)
    warnings = []

    findings = collect_workspace_objects(client, warnings, batch_size=10, batch_sleep_ms=0)

    kinds = {f.kind for f in findings}
    assert "workspace_dir" in kinds
    assert "workspace_notebook" in kinds
    notebook_item = next(f for f in findings if f.kind == "workspace_notebook")
    assert notebook_item.lockin_count >= 2
    assert "aws" in notebook_item.lockin_details
    assert warnings == []


def test_collect_jobs_with_runs():
    client = FakeClient({"/": []})
    client.jobs = Service([Obj(job_id=1, settings=Obj(name="Job1"))])
    client.jobs.list_runs = lambda *args, **kwargs: [Obj(run_id=10, job_id=1, state=Obj(life_cycle_state="RUNNING"))]
    warnings = []

    findings = collect_jobs(client, include_runs=True, warnings=warnings, batch_size=10, batch_sleep_ms=0)

    kinds = [f.kind for f in findings]
    assert "job" in kinds
    assert "job_run" in kinds


def test_collect_clusters_aws_instance_profiles(monkeypatch):
    monkeypatch.setenv("DATABRICKS_CLOUD_PROVIDER", "AWS")
    client = FakeClient({"/": []})
    client.clusters = Service([Obj(cluster_id="c1", cluster_name="C1")])
    client.cluster_policies = Service([Obj(policy_id="p1", name="P1")])
    client.global_init_scripts = Service([Obj(script_id="s1", name="S1")])
    client.instance_profiles = Service([Obj(instance_profile_arn="arn:aws:iam::123")])
    client.instance_pools = Service([Obj(instance_pool_id="ip1", instance_pool_name="Pool1")])
    warnings = []

    findings = collect_clusters(client, warnings=warnings, batch_size=10, batch_sleep_ms=0)

    kinds = {f.kind for f in findings}
    assert "cluster" in kinds
    assert "cluster_policy" in kinds
    assert "global_init_script" in kinds
    assert "instance_profile" in kinds
    assert "instance_pool" in kinds


def test_collect_findings_selective():
    ws = {
        "/": [Obj(object_type="DIRECTORY", path="/dir"), Obj(object_type="NOTEBOOK", path="/nb", language="PY")],
        "/dir": [],
    }
    client = FakeClient(ws)
    client.jobs = Service([Obj(job_id=1, settings=Obj(name="Job1"))])
    client.clusters = Service([Obj(cluster_id="c1", cluster_name="C1")])

    findings, warnings = collect_findings_selective(
        client,
        collectors="jobs,clusters",
        include_runs=False,
        include_query_history=False,
        batch_size=10,
        batch_sleep_ms=0,
    )

    kinds = {f.kind for f in findings}
    assert "job" in kinds
    assert "cluster" in kinds
    assert "workspace_notebook" not in kinds


def test_collect_findings_selective_invalid_collector():
    client = FakeClient({"/": []})

    findings, warnings = collect_findings_selective(
        client,
        collectors="invalid,jobs",
        include_runs=False,
        include_query_history=False,
        batch_size=10,
        batch_sleep_ms=0,
    )

    assert any("Unknown collector: invalid" in w for w in warnings)
