from lakeventory.models import Finding


def test_finding_fields():
    item = Finding("/path", "kind", "notes")
    assert item.path == "/path"
    assert item.kind == "kind"
    assert item.notes == "notes"
    assert item.lockin_count == 0
    assert item.lockin_details == ""


def test_finding_lockin_fields():
    item = Finding("/nb", "workspace_notebook", "language: PYTHON", lockin_count=3, lockin_details="aws:3")
    assert item.lockin_count == 3
    assert item.lockin_details == "aws:3"
