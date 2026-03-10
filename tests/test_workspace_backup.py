from pathlib import Path

from lakeventory.workspace_backup import backup_workspace


class Obj:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class WorkspaceApi:
    def __init__(self, tree, files, supports_direct_download=True):
        self._tree = tree
        self._files = files
        self._supports_direct_download = supports_direct_download

    def list(self, path="/"):
        return self._tree.get(path, [])

    def export(self, path="/", format="SOURCE", direct_download=False):
        if direct_download and not self._supports_direct_download:
            raise TypeError("unexpected keyword argument 'direct_download'")
        return self._files[path]


class Client:
    def __init__(self, workspace):
        self.workspace = workspace


def test_backup_workspace_recursive_and_zip(tmp_path: Path):
    tree = {
        "/": [
            Obj(object_type="DIRECTORY", path="/dir"),
            Obj(object_type="NOTEBOOK", path="/nb", language="PYTHON"),
        ],
        "/dir": [Obj(object_type="FILE", path="/dir/data.txt")],
    }
    files = {
        "/nb": b"print('hello')\n",
        "/dir/data.txt": b"payload",
    }
    client = Client(WorkspaceApi(tree, files))

    folder, archive, warnings = backup_workspace(client, "123", tmp_path)

    assert folder.exists()
    assert archive.exists()
    assert (folder / "nb.dbc").read_bytes() == b"print('hello')\n"
    assert (folder / "dir" / "data.txt.dbc").read_bytes() == b"payload"
    assert warnings == []


def test_backup_workspace_fallback_without_direct_download(tmp_path: Path):
    tree = {
        "/": [Obj(object_type="FILE", path="/file.txt")],
    }
    files = {
        "/file.txt": Obj(content="Zm9v"),  # base64('foo')
    }
    client = Client(WorkspaceApi(tree, files, supports_direct_download=False))

    folder, archive, warnings = backup_workspace(client, "123", tmp_path)

    assert folder.exists()
    assert archive.exists()
    assert (folder / "file.txt.dbc").read_bytes() == b"foo"
    assert warnings == []
