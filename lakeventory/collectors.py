"""Asset collection functions for Databricks workspace."""

import base64
import logging
from typing import List, Tuple

from databricks.sdk import WorkspaceClient

from .lockin import analyze_cloud_lockin, _format_lockin_details
from .models import Finding
from .utils import safe_iter, _safe_list_call


logger = logging.getLogger(__name__)


def _serialize_acl_entry(entry) -> str:
    """Serialize a single ACL entry from permissions/grants responses."""
    principal = (
        getattr(entry, "user_name", "")
        or getattr(entry, "group_name", "")
        or getattr(entry, "service_principal_name", "")
        or getattr(entry, "principal", "")
        or "unknown_principal"
    )

    permission_names = []

    all_permissions = getattr(entry, "all_permissions", None) or []
    for perm in all_permissions:
        perm_name = getattr(perm, "permission_level", None) or getattr(perm, "privilege", None) or str(perm)
        permission_names.append(str(perm_name))

    direct_privileges = getattr(entry, "privileges", None) or []
    if direct_privileges:
        permission_names.extend([str(p) for p in direct_privileges])

    if not permission_names:
        permission_names.append("NO_PERMISSION_DATA")

    return f"{principal}:{'|'.join(sorted(set(permission_names)))}"


def _collect_object_permissions(
    client: WorkspaceClient,
    warnings: List[str],
    request_object_type: str,
    request_object_id: str,
    object_ref: str,
) -> List[Finding]:
    """Collect ACLs for workspace-level objects using Permissions API."""
    if not hasattr(client, "permissions") or not hasattr(client.permissions, "get"):
        return []

    response = None
    attempts = [
        lambda: client.permissions.get(
            request_object_type=request_object_type,
            request_object_id=request_object_id,
        ),
        lambda: client.permissions.get(request_object_type, request_object_id),
        lambda: client.permissions.get(
            object_type=request_object_type,
            object_id=request_object_id,
        ),
    ]

    for attempt in attempts:
        try:
            response = attempt()
            break
        except TypeError:
            continue
        except Exception as exc:
            warnings.append(
                f"permissions.get failed for {request_object_type}:{request_object_id}: {exc}"
            )
            return []

    if response is None:
        return []

    acl_entries = getattr(response, "access_control_list", None) or []
    if not acl_entries:
        return []

    serialized = [_serialize_acl_entry(entry) for entry in acl_entries]
    return [
        Finding(
            path=f"acl:{request_object_type}:{request_object_id}",
            kind="acl",
            notes=f"object={object_ref} entries={'; '.join(serialized)}",
        )
    ]


def _collect_uc_grants(
    client: WorkspaceClient,
    warnings: List[str],
    securable_type: str,
    full_name: str,
) -> List[Finding]:
    """Collect ACLs for Unity Catalog securables using Grants API."""
    if not hasattr(client, "grants") or not hasattr(client.grants, "get"):
        return []

    response = None
    attempts = [
        lambda: client.grants.get(securable_type=securable_type, full_name=full_name),
        lambda: client.grants.get(securable_type, full_name),
    ]

    for attempt in attempts:
        try:
            response = attempt()
            break
        except TypeError:
            continue
        except Exception as exc:
            warnings.append(f"grants.get failed for {securable_type}:{full_name}: {exc}")
            return []

    if response is None:
        return []

    assignments = getattr(response, "privilege_assignments", None) or []
    if not assignments:
        return []

    serialized = [_serialize_acl_entry(assignment) for assignment in assignments]
    return [
        Finding(
            path=f"acl:uc:{securable_type}:{full_name}",
            kind="acl",
            notes=f"object={full_name} entries={'; '.join(serialized)}",
        )
    ]


def _read_notebook_source(client: WorkspaceClient, notebook_path: str, warnings: List[str]) -> str:
    """Read notebook source for lock-in analysis when available."""
    if not hasattr(client, "workspace") or not hasattr(client.workspace, "export"):
        return ""

    try:
        export_obj = client.workspace.export(path=notebook_path, format="SOURCE")
        raw_content = getattr(export_obj, "content", "") or ""
        if not raw_content:
            return ""
        try:
            return base64.b64decode(raw_content).decode("utf-8", errors="ignore")
        except Exception:
            return str(raw_content)
    except Exception as exc:
        warnings.append(f"workspace.export failed for {notebook_path}: {exc}")
        return ""


def collect_workspace_objects(
    client: WorkspaceClient,
    warnings: List[str],
    batch_size: int,
    batch_sleep_ms: int
) -> List[Finding]:
    """Collect workspace objects (notebooks, directories, files)."""
    findings = []
    stack = ["/"]
    
    while stack:
        current = stack.pop()
        for obj in safe_iter(
            "workspace.list",
            _safe_list_call("workspace.list", lambda p=current: client.workspace.list(path=p), warnings),
            warnings,
            batch_size,
            batch_sleep_ms,
        ):
            obj_type = getattr(obj, "object_type", None)
            obj_path = getattr(obj, "path", "") or ""
            if str(obj_type) == "DIRECTORY":
                stack.append(obj_path)
                findings.append(Finding(obj_path, "workspace_dir", "workspace directory"))
                object_id = str(getattr(obj, "object_id", "") or obj_path)
                findings.extend(
                    _collect_object_permissions(
                        client,
                        warnings,
                        "directories",
                        object_id,
                        obj_path,
                    )
                )
            else:
                kind = "workspace_notebook" if str(obj_type) == "NOTEBOOK" else "workspace_file"
                lang = getattr(obj, "language", "unknown")
                object_id = str(getattr(obj, "object_id", "") or obj_path)
                if kind == "workspace_notebook":
                    notebook_source = _read_notebook_source(client, obj_path, warnings)
                    analysis = analyze_cloud_lockin(notebook_source)
                    findings.append(
                        Finding(
                            obj_path,
                            kind,
                            f"language: {lang}",
                            lockin_count=analysis.get("total", 0),
                            lockin_details=_format_lockin_details(analysis),
                        )
                    )
                    findings.extend(
                        _collect_object_permissions(
                            client,
                            warnings,
                            "notebooks",
                            object_id,
                            obj_path,
                        )
                    )
                else:
                    findings.append(Finding(obj_path, kind, f"language: {lang}"))
                    findings.extend(
                        _collect_object_permissions(
                            client,
                            warnings,
                            "files",
                            object_id,
                            obj_path,
                        )
                    )
    
    return findings


def collect_jobs(
    client: WorkspaceClient,
    include_runs: bool,
    warnings: List[str],
    batch_size: int,
    batch_sleep_ms: int
) -> List[Finding]:
    """Collect jobs and optionally job runs."""
    findings = []
    
    for job in safe_iter(
        "jobs.list",
        _safe_list_call("jobs.list", lambda: client.jobs.list(), warnings),
        warnings,
        batch_size,
        batch_sleep_ms
    ):
        job_id = getattr(job, "job_id", None)
        name = getattr(getattr(job, "settings", None), "name", "")
        findings.append(Finding(f"job:{job_id}", "job", name))
        if job_id is not None:
            findings.extend(
                _collect_object_permissions(
                    client,
                    warnings,
                    "jobs",
                    str(job_id),
                    f"job:{job_id}",
                )
            )

    if include_runs and hasattr(client.jobs, "list_runs"):
        for run in safe_iter(
            "jobs.list_runs",
            _safe_list_call("jobs.list_runs", lambda: client.jobs.list_runs(), warnings),
            warnings,
            batch_size,
            batch_sleep_ms
        ):
            run_id = getattr(run, "run_id", None)
            job_id = getattr(run, "job_id", None)
            state = getattr(getattr(run, "state", None), "life_cycle_state", "")
            findings.append(Finding(f"job-run:{run_id}", "job_run", f"job_id={job_id} state={state}"))
    
    return findings


def collect_clusters(
    client: WorkspaceClient,
    warnings: List[str],
    batch_size: int,
    batch_sleep_ms: int,
    cloud_provider: str = "",
) -> List[Finding]:
    """Collect clusters, policies, init scripts, and instance pools."""
    findings = []
    cloud_provider = (cloud_provider or "").upper()
    
    # Clusters
    for cluster in safe_iter(
        "clusters.list",
        _safe_list_call("clusters.list", lambda: client.clusters.list(), warnings),
        warnings,
        batch_size,
        batch_sleep_ms
    ):
        cluster_id = getattr(cluster, "cluster_id", None)
        name = getattr(cluster, "cluster_name", "")
        findings.append(Finding(f"cluster:{cluster_id}", "cluster", name))
        if cluster_id:
            findings.extend(
                _collect_object_permissions(
                    client,
                    warnings,
                    "clusters",
                    str(cluster_id),
                    f"cluster:{cluster_id}",
                )
            )

    # Cluster policies
    for policy in safe_iter(
        "cluster_policies.list",
        _safe_list_call("cluster_policies.list", lambda: client.cluster_policies.list(), warnings),
        warnings,
        batch_size,
        batch_sleep_ms,
    ):
        policy_id = getattr(policy, "policy_id", None)
        name = getattr(policy, "name", "")
        findings.append(Finding(f"cluster-policy:{policy_id}", "cluster_policy", name))
        if policy_id is not None:
            findings.extend(
                _collect_object_permissions(
                    client,
                    warnings,
                    "cluster-policies",
                    str(policy_id),
                    f"cluster-policy:{policy_id}",
                )
            )

    # Global init scripts
    if hasattr(client, "global_init_scripts"):
        for script in safe_iter(
            "global_init_scripts.list",
            _safe_list_call("global_init_scripts.list", lambda: client.global_init_scripts.list(), warnings),
            warnings,
            batch_size,
            batch_sleep_ms,
        ):
            script_id = getattr(script, "script_id", None)
            name = getattr(script, "name", "")
            findings.append(Finding(f"global-init-script:{script_id}", "global_init_script", name))

    # Instance Profiles (AWS only)
    if cloud_provider == "AWS" and hasattr(client, "instance_profiles"):
        for prof in safe_iter(
            "instance_profiles.list",
            _safe_list_call("instance_profiles.list", lambda: client.instance_profiles.list(), warnings),
            warnings,
            batch_size,
            batch_sleep_ms,
        ):
            arn = getattr(prof, "instance_profile_arn", "")
            findings.append(Finding(f"instance-profile:{arn}", "instance_profile", arn))
    elif cloud_provider in ["AZURE", "GCP"] and hasattr(client, "instance_profiles"):
        logger.info("instance_profiles.list skipped: not available on %s", cloud_provider)

    # Instance Pools
    for pool in safe_iter(
        "instance_pools.list",
        _safe_list_call("instance_pools.list", lambda: client.instance_pools.list(), warnings),
        warnings,
        batch_size,
        batch_sleep_ms
    ):
        pool_id = getattr(pool, "instance_pool_id", None)
        name = getattr(pool, "instance_pool_name", "")
        findings.append(Finding(f"instance-pool:{pool_id}", "instance_pool", name))
        if pool_id is not None:
            findings.extend(
                _collect_object_permissions(
                    client,
                    warnings,
                    "instance-pools",
                    str(pool_id),
                    f"instance-pool:{pool_id}",
                )
            )
    
    return findings


def collect_sql_assets(
    client: WorkspaceClient,
    include_query_history: bool,
    warnings: List[str],
    batch_size: int,
    batch_sleep_ms: int
) -> List[Finding]:
    """Collect SQL warehouses, dashboards, queries, and alerts."""
    findings = []
    
    # SQL Warehouses
    for wh in safe_iter(
        "warehouses.list",
        _safe_list_call("warehouses.list", lambda: client.warehouses.list(), warnings),
        warnings,
        batch_size,
        batch_sleep_ms,
    ):
        wh_id = getattr(wh, "id", None)
        name = getattr(wh, "name", "")
        serverless = getattr(wh, "enable_serverless_compute", None)
        notes = f"{name} | serverless={serverless}"
        findings.append(Finding(f"sql-warehouse:{wh_id}", "sql_warehouse", notes))
        if wh_id is not None:
            findings.extend(
                _collect_object_permissions(
                    client,
                    warnings,
                    "warehouses",
                    str(wh_id),
                    f"sql-warehouse:{wh_id}",
                )
            )

    # Pipelines (Delta Live Tables)
    for pipeline in safe_iter(
        "pipelines.list",
        _safe_list_call("pipelines.list", lambda: client.pipelines.list_pipelines(), warnings),
        warnings,
        batch_size,
        batch_sleep_ms,
    ):
        pipeline_id = getattr(pipeline, "pipeline_id", None)
        name = getattr(pipeline, "name", "")
        findings.append(Finding(f"pipeline:{pipeline_id}", "pipeline", name))
        if pipeline_id is not None:
            findings.extend(
                _collect_object_permissions(
                    client,
                    warnings,
                    "pipelines",
                    str(pipeline_id),
                    f"pipeline:{pipeline_id}",
                )
            )

    # SQL Dashboards
    for dash in safe_iter(
        "dashboards.list",
        _safe_list_call("dashboards.list", lambda: client.dashboards.list(), warnings),
        warnings,
        batch_size,
        batch_sleep_ms,
    ):
        dash_id = getattr(dash, "id", None)
        name = getattr(dash, "name", "")
        findings.append(Finding(f"sql-dashboard:{dash_id}", "sql_dashboard", name))
        if dash_id is not None:
            findings.extend(
                _collect_object_permissions(
                    client,
                    warnings,
                    "dashboards",
                    str(dash_id),
                    f"sql-dashboard:{dash_id}",
                )
            )

    # Lakeview Dashboards
    for dash in safe_iter(
        "lakeview.list",
        _safe_list_call("lakeview.list", lambda: client.lakeview.list(), warnings),
        warnings,
        batch_size,
        batch_sleep_ms,
    ):
        dash_id = getattr(dash, "dashboard_id", None) or getattr(dash, "id", None)
        name = getattr(dash, "display_name", "") or getattr(dash, "name", "")
        findings.append(Finding(f"lakeview-dashboard:{dash_id}", "lakeview_dashboard", name))

    # Queries
    for query in safe_iter(
        "queries.list",
        _safe_list_call("queries.list", lambda: client.queries.list(), warnings),
        warnings,
        batch_size,
        batch_sleep_ms,
    ):
        query_id = getattr(query, "id", None)
        name = getattr(query, "name", "") or getattr(query, "display_name", "")
        findings.append(Finding(f"sql-query:{query_id}", "sql_query", name))
        if query_id is not None:
            findings.extend(
                _collect_object_permissions(
                    client,
                    warnings,
                    "queries",
                    str(query_id),
                    f"sql-query:{query_id}",
                )
            )

    # Query History
    if include_query_history and hasattr(client, "query_history"):
        for qh in safe_iter(
            "query_history.list",
            _safe_list_call("query_history.list", lambda: client.query_history.list(), warnings),
            warnings,
            batch_size,
            batch_sleep_ms,
        ):
            query_id = getattr(qh, "query_id", None)
            status = getattr(qh, "status", None)
            findings.append(Finding(f"query-history:{query_id}", "query_history", str(status)))

    # Alerts
    for alert in safe_iter(
        "alerts.list",
        _safe_list_call("alerts.list", lambda: client.alerts.list(), warnings),
        warnings,
        batch_size,
        batch_sleep_ms,
    ):
        alert_id = getattr(alert, "id", None)
        name = getattr(alert, "name", "") or getattr(alert, "display_name", "")
        findings.append(Finding(f"sql-alert:{alert_id}", "sql_alert", name))
        if alert_id is not None:
            findings.extend(
                _collect_object_permissions(
                    client,
                    warnings,
                    "alerts",
                    str(alert_id),
                    f"sql-alert:{alert_id}",
                )
            )
    
    return findings


def collect_mlflow_assets(
    client: WorkspaceClient,
    warnings: List[str],
    batch_size: int,
    batch_sleep_ms: int
) -> List[Finding]:
    """Collect MLflow experiments, models, and versions."""
    findings = []

    def _list_feature_store_items():
        if hasattr(client, "feature_store") and hasattr(client.feature_store, "list"):
            return client.feature_store.list()
        if hasattr(client, "registered_models"):
            logger.info(
                "feature_store.list unavailable; using registered_models.list() fallback (Model Registry listmodels)"
            )
            return client.registered_models.list()
        raise AttributeError("Feature Store API and Model Registry fallback not available")
    
    # Experiments
    for exp in safe_iter(
        "experiments.list",
        _safe_list_call("experiments.list", lambda: client.experiments.list_experiments(), warnings),
        warnings,
        batch_size,
        batch_sleep_ms,
    ):
        exp_id = getattr(exp, "experiment_id", None)
        name = getattr(exp, "name", "")
        findings.append(Finding(f"mlflow-experiment:{exp_id}", "mlflow_experiment", name))

    # Registered Models
    for model in safe_iter(
        "registered_models.list",
        _safe_list_call("registered_models.list", lambda: client.registered_models.list(), warnings),
        warnings,
        batch_size,
        batch_sleep_ms,
    ):
        model_name = getattr(model, "name", "")
        findings.append(Finding(f"mlflow-model:{model_name}", "mlflow_model", model_name))
        
        # Model Versions
        if hasattr(client, "model_versions") and model_name:
            for mv in safe_iter(
                f"model_versions.list({model_name})",
                _safe_list_call(
                    f"model_versions.list({model_name})",
                    lambda mn=model_name: client.model_versions.list(full_name=mn),
                    warnings
                ),
                warnings,
                batch_size,
                batch_sleep_ms,
            ):
                version = getattr(mv, "version", "")
                findings.append(Finding(f"model-version:{model_name}:{version}", "model_version", model_name))

    # Feature Store
    if hasattr(client, "feature_store") or hasattr(client, "registered_models"):
        for fs in safe_iter(
            "feature_store.list",
            _safe_list_call("feature_store.list", _list_feature_store_items, warnings),
            warnings,
            batch_size,
            batch_sleep_ms,
        ):
            name = getattr(fs, "name", "")
            findings.append(Finding(f"feature-store:{name}", "feature_store", name))

    # Feature Engineering
    if hasattr(client, "feature_engineering"):
        for fe in safe_iter(
            "feature_engineering.list",
            _safe_list_call("feature_engineering.list", lambda: client.feature_engineering.list(), warnings),
            warnings,
            batch_size,
            batch_sleep_ms,
        ):
            name = getattr(fe, "name", "")
            findings.append(Finding(f"feature-engineering:{name}", "feature_engineering", name))
    
    return findings


def collect_unity_catalog(
    client: WorkspaceClient,
    warnings: List[str],
    batch_size: int,
    batch_sleep_ms: int
) -> List[Finding]:
    """Collect Unity Catalog assets."""
    findings = []
    
    for catalog_obj in safe_iter(
        "catalogs.list",
        _safe_list_call("catalogs.list", lambda: client.catalogs.list(), warnings),
        warnings,
        batch_size,
        batch_sleep_ms,
    ):
        catalog_name = getattr(catalog_obj, "name", "")
        findings.append(Finding(f"uc-catalog:{catalog_name}", "uc_catalog", catalog_name))
        findings.extend(_collect_uc_grants(client, warnings, "CATALOG", catalog_name))

        # Schemas
        for schema in safe_iter(
            f"schemas.list({catalog_name})",
            _safe_list_call(f"schemas.list({catalog_name})", lambda cn=catalog_name: client.schemas.list(catalog_name=cn), warnings),
            warnings,
            batch_size,
            batch_sleep_ms,
        ):
            schema_name = getattr(schema, "name", "")
            findings.append(Finding(f"uc-schema:{catalog_name}.{schema_name}", "uc_schema", schema_name))
            schema_full_name = f"{catalog_name}.{schema_name}"
            findings.extend(_collect_uc_grants(client, warnings, "SCHEMA", schema_full_name))

            # Tables
            for table in safe_iter(
                f"tables.list({catalog_name}.{schema_name})",
                _safe_list_call(
                    f"tables.list({catalog_name}.{schema_name})",
                    lambda cn=catalog_name, sn=schema_name: client.tables.list(catalog_name=cn, schema_name=sn),
                    warnings
                ),
                warnings,
                batch_size,
                batch_sleep_ms,
            ):
                table_name = getattr(table, "name", "")
                findings.append(
                    Finding(
                        f"uc-table:{catalog_name}.{schema_name}.{table_name}",
                        "uc_table",
                        getattr(table, "table_type", ""),
                    )
                )
                table_full_name = f"{catalog_name}.{schema_name}.{table_name}"
                findings.extend(_collect_uc_grants(client, warnings, "TABLE", table_full_name))

            # Volumes
            for vol in safe_iter(
                f"volumes.list({catalog_name}.{schema_name})",
                _safe_list_call(
                    f"volumes.list({catalog_name}.{schema_name})",
                    lambda cn=catalog_name, sn=schema_name: client.volumes.list(catalog_name=cn, schema_name=sn),
                    warnings
                ),
                warnings,
                batch_size,
                batch_sleep_ms,
            ):
                vol_name = getattr(vol, "name", "")
                findings.append(Finding(f"uc-volume:{vol_name}", "uc_volume", vol_name))
                volume_full_name = f"{catalog_name}.{schema_name}.{vol_name}"
                findings.extend(_collect_uc_grants(client, warnings, "VOLUME", volume_full_name))
    
    # External Locations
    for eloc in safe_iter(
        "external_locations.list",
        _safe_list_call("external_locations.list", lambda: client.external_locations.list(), warnings),
        warnings,
        batch_size,
        batch_sleep_ms,
    ):
        name = getattr(eloc, "name", "")
        url = getattr(eloc, "url", "")
        findings.append(Finding(f"external-location:{name}", "external_location", url))
        findings.extend(_collect_uc_grants(client, warnings, "EXTERNAL_LOCATION", name))

    # Storage Credentials
    for cred in safe_iter(
        "storage_credentials.list",
        _safe_list_call("storage_credentials.list", lambda: client.storage_credentials.list(), warnings),
        warnings,
        batch_size,
        batch_sleep_ms,
    ):
        name = getattr(cred, "name", "")
        findings.append(Finding(f"storage-credential:{name}", "storage_credential", name))
        findings.extend(_collect_uc_grants(client, warnings, "STORAGE_CREDENTIAL", name))

    # Connections
    for conn in safe_iter(
        "connections.list",
        _safe_list_call("connections.list", lambda: client.connections.list(), warnings),
        warnings,
        batch_size,
        batch_sleep_ms,
    ):
        name = getattr(conn, "name", "")
        type_name = getattr(conn, "connection_type", "")
        findings.append(Finding(f"connection:{name}", "connection", str(type_name)))
        findings.extend(_collect_uc_grants(client, warnings, "CONNECTION", name))

    # Metastores
    if hasattr(client, "metastores"):
        for ms in safe_iter(
            "metastores.list",
            _safe_list_call("metastores.list", lambda: client.metastores.list(), warnings),
            warnings,
            batch_size,
            batch_sleep_ms,
        ):
            name = getattr(ms, "name", "")
            ms_id = getattr(ms, "metastore_id", "")
            findings.append(Finding(f"metastore:{ms_id}", "metastore", name))
            if ms_id:
                findings.extend(_collect_uc_grants(client, warnings, "METASTORE", str(ms_id)))
    
    return findings


def collect_repos(
    client: WorkspaceClient,
    warnings: List[str],
    batch_size: int,
    batch_sleep_ms: int
) -> List[Finding]:
    """Collect Git repositories and credentials."""
    findings = []
    
    # Repos
    for repo in safe_iter(
        "repos.list",
        _safe_list_call("repos.list", lambda: client.repos.list(), warnings),
        warnings,
        batch_size,
        batch_sleep_ms,
    ):
        repo_id = getattr(repo, "id", None)
        path = getattr(repo, "path", "")
        findings.append(Finding(f"repo:{repo_id}", "repo", path))
        if repo_id is not None:
            findings.extend(
                _collect_object_permissions(
                    client,
                    warnings,
                    "repos",
                    str(repo_id),
                    f"repo:{repo_id}",
                )
            )

    # Git Credentials
    if hasattr(client, "git_credentials"):
        for cred in safe_iter(
            "git_credentials.list",
            _safe_list_call("git_credentials.list", lambda: client.git_credentials.list(), warnings),
            warnings,
            batch_size,
            batch_sleep_ms,
        ):
            cred_id = getattr(cred, "credential_id", None)
            user = getattr(cred, "git_username", "")
            findings.append(Finding(f"git-credential:{cred_id}", "git_credential", user))
    
    return findings


def collect_security_assets(
    client: WorkspaceClient,
    warnings: List[str],
    batch_size: int,
    batch_sleep_ms: int
) -> List[Finding]:
    """Collect secret scopes, tokens, and IP access lists."""
    findings = []
    
    # Secret Scopes
    for scope in safe_iter(
        "secrets.list_scopes",
        _safe_list_call("secrets.list_scopes", lambda: client.secrets.list_scopes(), warnings),
        warnings,
        batch_size,
        batch_sleep_ms,
    ):
        name = getattr(scope, "name", "")
        findings.append(Finding(f"secret-scope:{name}", "secret_scope", name))
        if hasattr(client.secrets, "list_acls"):
            for acl in safe_iter(
                f"secrets.list_acls({name})",
                _safe_list_call(
                    f"secrets.list_acls({name})",
                    lambda sn=name: client.secrets.list_acls(scope=sn),
                    warnings,
                ),
                warnings,
                batch_size,
                batch_sleep_ms,
            ):
                principal = getattr(acl, "principal", "")
                permission = getattr(acl, "permission", "")
                findings.append(
                    Finding(
                        f"acl:secret-scope:{name}:{principal}",
                        "acl",
                        f"object=secret-scope:{name} entries={principal}:{permission}",
                    )
                )

    # Tokens
    for token in safe_iter(
        "tokens.list",
        _safe_list_call("tokens.list", lambda: client.tokens.list(), warnings),
        warnings,
        batch_size,
        batch_sleep_ms,
    ):
        token_id = getattr(token, "token_id", None)
        creator = getattr(token, "created_by_username", "")
        findings.append(Finding(f"token:{token_id}", "token", f"created_by={creator}"))

    # IP Access Lists
    if hasattr(client, "ip_access_lists"):
        for ip in safe_iter(
            "ip_access_lists.list",
            _safe_list_call("ip_access_lists.list", lambda: client.ip_access_lists.list(), warnings),
            warnings,
            batch_size,
            batch_sleep_ms,
        ):
            list_id = getattr(ip, "list_id", "")
            label = getattr(ip, "label", "")
            findings.append(Finding(f"ip-access-list:{list_id}", "ip_access_list", label))
    
    return findings


def collect_identities(
    client: WorkspaceClient,
    warnings: List[str],
    batch_size: int,
    batch_sleep_ms: int
) -> List[Finding]:
    """Collect users, groups, and service principals."""
    findings = []
    
    # Users
    for user_obj in safe_iter(
        "users.list",
        _safe_list_call("users.list", lambda: client.users.list(), warnings),
        warnings,
        batch_size,
        batch_sleep_ms
    ):
        name = getattr(user_obj, "user_name", "") or getattr(user_obj, "userName", "")
        user_id = getattr(user_obj, "id", "")
        findings.append(Finding(f"user:{user_id}", "user", name))

    # Groups
    for group in safe_iter(
        "groups.list",
        _safe_list_call("groups.list", lambda: client.groups.list(), warnings),
        warnings,
        batch_size,
        batch_sleep_ms
    ):
        name = getattr(group, "display_name", "") or getattr(group, "displayName", "")
        group_id = getattr(group, "id", "")
        findings.append(Finding(f"group:{group_id}", "group", name))

    # Service Principals
    for sp in safe_iter(
        "service_principals.list",
        _safe_list_call("service_principals.list", lambda: client.service_principals.list(), warnings),
        warnings,
        batch_size,
        batch_sleep_ms,
    ):
        name = getattr(sp, "display_name", "") or getattr(sp, "displayName", "")
        sp_id = getattr(sp, "id", "")
        findings.append(Finding(f"service-principal:{sp_id}", "service_principal", name))
    
    return findings


def collect_serving_assets(
    client: WorkspaceClient,
    warnings: List[str],
    batch_size: int,
    batch_sleep_ms: int
) -> List[Finding]:
    """Collect serving endpoints, vector search, and online tables."""
    findings = []

    def _list_vector_search_endpoints():
        api = client.vector_search_endpoints
        if hasattr(api, "list"):
            return api.list()
        if hasattr(api, "list_endpoints"):
            return api.list_endpoints()
        raise AttributeError("VectorSearchEndpointsAPI has no supported list method")
    
    # Serving Endpoints
    for endpoint in safe_iter(
        "serving_endpoints.list",
        _safe_list_call("serving_endpoints.list", lambda: client.serving_endpoints.list(), warnings),
        warnings,
        batch_size,
        batch_sleep_ms,
    ):
        name = getattr(endpoint, "name", "")
        findings.append(Finding(f"serving-endpoint:{name}", "serving_endpoint", name))
        if name:
            findings.extend(
                _collect_object_permissions(
                    client,
                    warnings,
                    "serving-endpoints",
                    str(name),
                    f"serving-endpoint:{name}",
                )
            )

    # Vector Search Endpoints
    if hasattr(client, "vector_search_endpoints"):
        for vse in safe_iter(
            "vector_search_endpoints.list",
            _safe_list_call("vector_search_endpoints.list", _list_vector_search_endpoints, warnings),
            warnings,
            batch_size,
            batch_sleep_ms,
        ):
            name = getattr(vse, "name", "")
            findings.append(Finding(f"vector-search-endpoint:{name}", "vector_search_endpoint", name))

    # Vector Search Indexes
    if hasattr(client, "vector_search_indexes"):
        for vsi in safe_iter(
            "vector_search_indexes.list",
            _safe_list_call("vector_search_indexes.list", lambda: client.vector_search_indexes.list(), warnings),
            warnings,
            batch_size,
            batch_sleep_ms,
        ):
            name = getattr(vsi, "name", "")
            findings.append(Finding(f"vector-search-index:{name}", "vector_search_index", name))

    # Online Tables
    if hasattr(client, "online_tables"):
        for ot in safe_iter(
            "online_tables.list",
            _safe_list_call("online_tables.list", lambda: client.online_tables.list(), warnings),
            warnings,
            batch_size,
            batch_sleep_ms,
        ):
            name = getattr(ot, "name", "")
            findings.append(Finding(f"online-table:{name}", "online_table", name))
    
    return findings


def collect_sharing(
    client: WorkspaceClient,
    warnings: List[str],
    batch_size: int,
    batch_sleep_ms: int
) -> List[Finding]:
    """Collect Delta Sharing assets."""
    findings = []
    
    # Shares
    if hasattr(client, "shares"):
        for share in safe_iter(
            "shares.list",
            _safe_list_call("shares.list", lambda: client.shares.list(), warnings),
            warnings,
            batch_size,
            batch_sleep_ms,
        ):
            name = getattr(share, "name", "")
            findings.append(Finding(f"share:{name}", "share", name))

    # Recipients
    if hasattr(client, "recipients"):
        for rec in safe_iter(
            "recipients.list",
            _safe_list_call("recipients.list", lambda: client.recipients.list(), warnings),
            warnings,
            batch_size,
            batch_sleep_ms,
        ):
            name = getattr(rec, "name", "")
            findings.append(Finding(f"recipient:{name}", "recipient", name))

    # Providers
    if hasattr(client, "providers"):
        for prov in safe_iter(
            "providers.list",
            _safe_list_call("providers.list", lambda: client.providers.list(), warnings),
            warnings,
            batch_size,
            batch_sleep_ms,
        ):
            name = getattr(prov, "name", "")
            findings.append(Finding(f"provider:{name}", "provider", name))
    
    return findings


def collect_dbfs(
    client: WorkspaceClient,
    warnings: List[str],
    batch_size: int,
    batch_sleep_ms: int
) -> List[Finding]:
    """Collect DBFS root listing."""
    findings = []
    
    if hasattr(client, "dbfs"):
        for file_info in safe_iter(
            "dbfs.list",
            _safe_list_call("dbfs.list", lambda: client.dbfs.list(path="/"), warnings),
            warnings,
            batch_size,
            batch_sleep_ms,
        ):
            path = getattr(file_info, "path", "")
            is_dir = getattr(file_info, "is_dir", False)
            kind = "dbfs_dir" if is_dir else "dbfs_file"
            findings.append(Finding(path, kind, "dbfs root"))
    
    return findings


def collect_acl_assets(
    client: WorkspaceClient,
    warnings: List[str],
    batch_size: int,
    batch_sleep_ms: int,
) -> List[Finding]:
    """Collect ACL findings only across supported services."""
    acl_findings: List[Finding] = []

    acl_findings.extend(
        [f for f in collect_workspace_objects(client, warnings, batch_size, batch_sleep_ms) if f.kind == "acl"]
    )
    acl_findings.extend(
        [
            f
            for f in collect_jobs(
                client,
                include_runs=False,
                warnings=warnings,
                batch_size=batch_size,
                batch_sleep_ms=batch_sleep_ms,
            )
            if f.kind == "acl"
        ]
    )
    acl_findings.extend(
        [f for f in collect_clusters(client, warnings, batch_size, batch_sleep_ms) if f.kind == "acl"]
    )
    acl_findings.extend(
        [
            f
            for f in collect_sql_assets(
                client,
                include_query_history=False,
                warnings=warnings,
                batch_size=batch_size,
                batch_sleep_ms=batch_sleep_ms,
            )
            if f.kind == "acl"
        ]
    )
    acl_findings.extend(
        [f for f in collect_unity_catalog(client, warnings, batch_size, batch_sleep_ms) if f.kind == "acl"]
    )
    acl_findings.extend(
        [f for f in collect_repos(client, warnings, batch_size, batch_sleep_ms) if f.kind == "acl"]
    )
    acl_findings.extend(
        [f for f in collect_security_assets(client, warnings, batch_size, batch_sleep_ms) if f.kind == "acl"]
    )
    acl_findings.extend(
        [f for f in collect_serving_assets(client, warnings, batch_size, batch_sleep_ms) if f.kind == "acl"]
    )

    return acl_findings


COLLECTOR_REGISTRY = {
    "workspace": collect_workspace_objects,
    "jobs": collect_jobs,
    "clusters": collect_clusters,
    "sql": collect_sql_assets,
    "mlflow": collect_mlflow_assets,
    "unity_catalog": collect_unity_catalog,
    "repos": collect_repos,
    "security": collect_security_assets,
    "identities": collect_identities,
    "serving": collect_serving_assets,
    "sharing": collect_sharing,
    "dbfs": collect_dbfs,
    "acl": collect_acl_assets,
}


def collect_all_findings(
    client: WorkspaceClient,
    include_runs: bool,
    include_query_history: bool,
    include_dbfs: bool,
    batch_size: int,
    batch_sleep_ms: int,
    cloud_provider: str = "",
) -> Tuple[List[Finding], List[str]]:
    """Collect all findings from Databricks workspace.
    
    Args:
        client: Databricks WorkspaceClient
        include_runs: Whether to include job runs
        include_query_history: Whether to include query history
        include_dbfs: Whether to include DBFS listing
        batch_size: Items per batch before sleeping
        batch_sleep_ms: Sleep time in ms between batches
        
    Returns:
        Tuple of (findings list, warnings list)
    """
    warnings: List[str] = []
    all_findings: List[Finding] = []
    
    # Collect from all sources
    all_findings.extend(collect_workspace_objects(client, warnings, batch_size, batch_sleep_ms))
    all_findings.extend(collect_jobs(client, include_runs, warnings, batch_size, batch_sleep_ms))
    all_findings.extend(collect_clusters(client, warnings, batch_size, batch_sleep_ms, cloud_provider))
    all_findings.extend(collect_sql_assets(client, include_query_history, warnings, batch_size, batch_sleep_ms))
    all_findings.extend(collect_mlflow_assets(client, warnings, batch_size, batch_sleep_ms))
    all_findings.extend(collect_unity_catalog(client, warnings, batch_size, batch_sleep_ms))
    all_findings.extend(collect_repos(client, warnings, batch_size, batch_sleep_ms))
    all_findings.extend(collect_security_assets(client, warnings, batch_size, batch_sleep_ms))
    all_findings.extend(collect_identities(client, warnings, batch_size, batch_sleep_ms))
    all_findings.extend(collect_serving_assets(client, warnings, batch_size, batch_sleep_ms))
    all_findings.extend(collect_sharing(client, warnings, batch_size, batch_sleep_ms))
    
    if include_dbfs:
        all_findings.extend(collect_dbfs(client, warnings, batch_size, batch_sleep_ms))
    
    return all_findings, warnings


def collect_findings_selective(
    client: WorkspaceClient,
    collectors: str,
    include_runs: bool,
    include_query_history: bool,
    batch_size: int,
    batch_sleep_ms: int,
    cloud_provider: str = "",
) -> Tuple[List[Finding], List[str]]:
    """Collect findings from selected collectors only.
    
    Args:
        client: Databricks WorkspaceClient
        collectors: Comma-separated list of collector names (workspace,jobs,clusters,sql,mlflow,unity_catalog,repos,security,identities,serving,sharing,dbfs)
        include_runs: Whether to include job runs
        include_query_history: Whether to include query history
        batch_size: Items per batch before sleeping
        batch_sleep_ms: Sleep time in ms between batches
        
    Returns:
        Tuple of (findings list, warnings list)
    """
    warnings: List[str] = []
    all_findings: List[Finding] = []
    
    collector_names = [c.strip() for c in collectors.split(",")]
    
    for name in collector_names:
        if name not in COLLECTOR_REGISTRY:
            warnings.append(f"Unknown collector: {name}")
            continue
        
        collector_fn = COLLECTOR_REGISTRY[name]
        
        if name == "jobs":
            all_findings.extend(collector_fn(client, include_runs, warnings, batch_size, batch_sleep_ms))
        elif name == "clusters":
            all_findings.extend(collector_fn(client, warnings, batch_size, batch_sleep_ms, cloud_provider))
        elif name == "sql":
            all_findings.extend(collector_fn(client, include_query_history, warnings, batch_size, batch_sleep_ms))
        else:
            all_findings.extend(collector_fn(client, warnings, batch_size, batch_sleep_ms))
    
    return all_findings, warnings
