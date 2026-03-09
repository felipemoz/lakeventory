from databricks_inventory.models import Finding


def test_finding_fields():
    item = Finding("/path", "kind", "notes")
    assert item.path == "/path"
    assert item.kind == "kind"
    assert item.notes == "notes"
