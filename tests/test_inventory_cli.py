from pathlib import Path

from lakeventory.inventory_cli import _resolve_path


def test_resolve_path_relative(tmp_path: Path):
    result = _resolve_path(tmp_path, "./backup")
    assert result == (tmp_path / "backup").resolve()


def test_resolve_path_absolute(tmp_path: Path):
    result = _resolve_path(tmp_path, "/tmp/lakeventory-backup")
    assert result == Path("/tmp/lakeventory-backup").resolve()
