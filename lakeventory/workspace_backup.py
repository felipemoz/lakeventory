"""Workspace backup utilities using Databricks workspace export API."""

import base64
import io
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Tuple


logger = logging.getLogger(__name__)


def _extract_export_bytes(export_obj) -> bytes:
    """Extract bytes from export response across SDK variants."""
    if export_obj is None:
        return b""

    if isinstance(export_obj, bytes):
        return export_obj
    if isinstance(export_obj, bytearray):
        return bytes(export_obj)
    if isinstance(export_obj, str):
        try:
            return base64.b64decode(export_obj)
        except Exception:
            return export_obj.encode("utf-8", errors="ignore")

    if hasattr(export_obj, "read"):
        content = export_obj.read()
        if isinstance(content, str):
            return content.encode("utf-8", errors="ignore")
        return content

    if hasattr(export_obj, "content"):
        content = getattr(export_obj, "content", "") or ""
        if isinstance(content, bytes):
            return content
        if isinstance(content, str):
            try:
                return base64.b64decode(content)
            except Exception:
                return content.encode("utf-8", errors="ignore")

    if hasattr(export_obj, "contents"):
        content = getattr(export_obj, "contents", b"") or b""
        if isinstance(content, str):
            return content.encode("utf-8", errors="ignore")
        return bytes(content)

    return b""


def _export_object_bytes(client, path: str, export_format: str) -> bytes:
    """Export workspace object trying direct_download first."""
    try:
        export_obj = client.workspace.export(path=path, format=export_format, direct_download=True)
        return _extract_export_bytes(export_obj)
    except TypeError:
        export_obj = client.workspace.export(path=path, format=export_format)
        return _extract_export_bytes(export_obj)


def backup_workspace(
    client,
    workspace_id: str,
    output_dir: Path,
) -> Tuple[Path, Path, List[str]]:
    """Backup workspace recursively and generate a zip archive.

    Returns:
        Tuple of (backup_folder, backup_zip_path, warnings)
    """
    warnings: List[str] = []
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_root = output_dir / f"workspace_backup_{workspace_id}_{timestamp}"
    backup_root.mkdir(parents=True, exist_ok=True)

    queue = ["/"]
    exported_files = 0

    while queue:
        current_path = queue.pop(0)
        try:
            objects = list(client.workspace.list(path=current_path))
        except Exception as exc:
            warnings.append(f"workspace.list failed for {current_path}: {exc}")
            continue

        for obj in objects:
            object_type = str(getattr(obj, "object_type", "") or "")
            object_path = getattr(obj, "path", "")
            if not object_path:
                continue

            rel = Path(object_path.lstrip("/"))

            if object_type == "DIRECTORY":
                (backup_root / rel).mkdir(parents=True, exist_ok=True)
                queue.append(object_path)
                continue

            if object_type not in {"NOTEBOOK", "FILE"}:
                warnings.append(f"workspace.export skipped unsupported type {object_type}: {object_path}")
                continue

            export_format = "DBC"
            try:
                payload = _export_object_bytes(client, object_path, export_format)
                if not payload:
                    warnings.append(f"workspace.export returned empty content: {object_path}")
                    continue

                file_path = backup_root / rel
                file_path = file_path.with_name(f"{file_path.name}.dbc")

                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_bytes(payload)
                exported_files += 1
            except Exception as exc:
                warnings.append(f"workspace.export failed for {object_path}: {exc}")

    archive_base = output_dir / backup_root.name
    archive_path = Path(shutil.make_archive(str(archive_base), "zip", root_dir=str(backup_root)))

    if exported_files == 0:
        warnings.append(
            "workspace backup exported 0 files; check object types returned by workspace.list or export permissions/format support"
        )

    logger.info("Workspace backup completed: %d files exported", exported_files)
    logger.info("Backup folder: %s", backup_root)
    logger.info("Backup archive: %s", archive_path)

    return backup_root, archive_path, warnings
