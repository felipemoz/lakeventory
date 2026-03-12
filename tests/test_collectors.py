import os
import base64

from lakeventory.collectors import (
    collect_workspace_objects,
    collect_jobs,
    collect_clusters,
    collect_findings_selective,
    collect_serving_assets,
    collect_mlflow_assets,
)
from lakeventory.models import Finding


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


class VectorSearchEndpointsService:
    def __init__(self, items=None):
        self._items = items or []

    def list_endpoints(self, *args, **kwargs):
        return self._items


class NoListFeatureStoreService:
    pass


class ExperimentsService:
    def __init__(self, items=None):
        self._items = items or []

    def list_experiments(self, *args, **kwargs):
        return self._items


class PermissionsService:
    def __init__(self, acl_by_key=None):
        self._acl_by_key = acl_by_key or {}

    def get(self, request_object_type=None, request_object_id=None, *args, **kwargs):
        if request_object_type is None and args:
            request_object_type = args[0]
        if request_object_id is None and len(args) > 1:
            request_object_id = args[1]

        key = (str(request_object_type), str(request_object_id))
        items = self._acl_by_key.get(key, [])
        return Obj(access_control_list=items)


class GrantsService:
    def __init__(self, grants_by_key=None):
        self._grants_by_key = grants_by_key or {}

    def get(self, securable_type=None, full_name=None, *args, **kwargs):
        if securable_type is None and args:
            securable_type = args[0]
        if full_name is None and len(args) > 1:
            full_name = args[1]

        key = (str(securable_type), str(full_name))
        items = self._grants_by_key.get(key, [])
        return Obj(privilege_assignments=items)


class SecretsService:
    def __init__(self, scopes=None, acls_by_scope=None):
        self._scopes = scopes or []
        self._acls_by_scope = acls_by_scope or {}

    def list_scopes(self, *args, **kwargs):
        return self._scopes

    def list_acls(self, scope=None, *args, **kwargs):
        return self._acls_by_scope.get(scope, [])


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
    client = FakeClient({"/": []})
    client.clusters = Service([Obj(cluster_id="c1", cluster_name="C1")])
    client.cluster_policies = Service([Obj(policy_id="p1", name="P1")])
    client.global_init_scripts = Service([Obj(script_id="s1", name="S1")])
    client.instance_profiles = Service([Obj(instance_profile_arn="arn:aws:iam::123")])
    client.instance_pools = Service([Obj(instance_pool_id="ip1", instance_pool_name="Pool1")])
    warnings = []

    findings = collect_clusters(client, warnings=warnings, batch_size=10, batch_sleep_ms=0, cloud_provider="AWS")

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


def test_collect_serving_assets_vector_search_list_endpoints_fallback():
    client = FakeClient({"/": []})
    client.serving_endpoints = Service([])
    client.vector_search_endpoints = VectorSearchEndpointsService([Obj(name="vse-1")])
    warnings = []

    findings = collect_serving_assets(
        client,
        warnings=warnings,
        batch_size=10,
        batch_sleep_ms=0,
    )

    kinds = {f.kind for f in findings}
    assert "vector_search_endpoint" in kinds
    assert warnings == []


def test_collect_mlflow_assets_feature_store_fallback_to_registered_models():
    client = FakeClient({"/": []})
    client.experiments = ExperimentsService([])
    client.registered_models = Service([Obj(name="model-a")])
    client.model_versions = Service([])
    client.feature_store = NoListFeatureStoreService()
    warnings = []

    findings = collect_mlflow_assets(
        client,
        warnings=warnings,
        batch_size=10,
        batch_sleep_ms=0,
    )

    kinds = [f.kind for f in findings]
    assert "mlflow_model" in kinds
    assert "feature_store" in kinds
    assert warnings == []


def test_collect_jobs_collects_acl_findings():
    client = FakeClient({"/": []})
    client.jobs = Service([Obj(job_id=42, settings=Obj(name="Job ACL"))])
    client.permissions = PermissionsService(
        {
            ("jobs", "42"): [
                Obj(
                    user_name="alice@example.com",
                    all_permissions=[Obj(permission_level="CAN_MANAGE")],
                )
            ]
        }
    )
    warnings = []

    findings = collect_jobs(client, include_runs=False, warnings=warnings, batch_size=10, batch_sleep_ms=0)

    acl_findings = [f for f in findings if f.kind == "acl"]
    assert len(acl_findings) == 1
    assert "alice@example.com:CAN_MANAGE" in acl_findings[0].notes
    assert warnings == []


def test_collect_security_assets_collects_secret_scope_acls():
    from lakeventory.collectors import collect_security_assets

    client = FakeClient({"/": []})
    client.secrets = SecretsService(
        scopes=[Obj(name="scope-a")],
        acls_by_scope={"scope-a": [Obj(principal="grp-data", permission="READ")]},
    )
    client.tokens = Service([])
    client.ip_access_lists = Service([])
    warnings = []

    findings = collect_security_assets(client, warnings=warnings, batch_size=10, batch_sleep_ms=0)

    acl_findings = [f for f in findings if f.kind == "acl"]
    assert len(acl_findings) == 1
    assert "object=secret-scope:scope-a" in acl_findings[0].notes
    assert "grp-data:READ" in acl_findings[0].notes
    assert warnings == []


def test_collect_unity_catalog_collects_grants_acl_findings():
    from lakeventory.collectors import collect_unity_catalog

    client = FakeClient({"/": []})
    client.catalogs = Service([Obj(name="main")])
    client.schemas = Service([])
    client.external_locations = Service([])
    client.storage_credentials = Service([])
    client.connections = Service([])
    client.grants = GrantsService(
        {
            ("CATALOG", "main"): [
                Obj(principal="grp-analytics", privileges=["USE_CATALOG", "CREATE_SCHEMA"])
            ]
        }
    )
    warnings = []

    findings = collect_unity_catalog(client, warnings=warnings, batch_size=10, batch_sleep_ms=0)

    acl_findings = [f for f in findings if f.kind == "acl"]
    assert len(acl_findings) == 1
    assert "grp-analytics:CREATE_SCHEMA|USE_CATALOG" in acl_findings[0].notes
    assert warnings == []


def test_collect_findings_selective_acl_collector():
    client = FakeClient({"/": []})
    client.jobs = Service([Obj(job_id=99, settings=Obj(name="Job ACL Selective"))])
    client.permissions = PermissionsService(
        {
            ("jobs", "99"): [
                Obj(
                    group_name="grp-platform",
                    all_permissions=[Obj(permission_level="CAN_VIEW")],
                )
            ]
        }
    )

    findings, warnings = collect_findings_selective(
        client,
        collectors="acl",
        include_runs=False,
        include_query_history=False,
        batch_size=10,
        batch_sleep_ms=0,
    )

    acl_findings = [f for f in findings if f.kind == "acl"]
    assert len(acl_findings) >= 1
    assert any("grp-platform:CAN_VIEW" in f.notes for f in acl_findings)
    assert not any("Unknown collector: acl" in w for w in warnings)
