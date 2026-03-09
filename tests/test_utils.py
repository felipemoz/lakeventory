from lakeventory import utils


def test_safe_iter_batches_and_sleep(monkeypatch):
    calls = []

    def fake_sleep(seconds):
        calls.append(seconds)

    monkeypatch.setattr(utils.time, "sleep", fake_sleep)
    warnings = []
    items = [1, 2, 3]

    output = list(utils.safe_iter("label", iter(items), warnings, batch_size=2, sleep_ms=10))

    assert output == items
    assert calls == [0.01]
    assert warnings == []


def test_safe_iter_handles_exception():
    warnings = []

    def bad_iter():
        yield 1
        raise ValueError("boom")

    output = list(utils.safe_iter("label", bad_iter(), warnings, batch_size=0, sleep_ms=0))

    assert output == [1]
    assert warnings
    assert "label failed" in warnings[0]

