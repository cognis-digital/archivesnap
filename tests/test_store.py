from archivesnap.store import SnapshotStore
from archivesnap.hashing import content_hash


def test_save_and_load_roundtrip(tmp_path):
    store = SnapshotStore(tmp_path)
    url = "https://example.com/a"
    snap = store.save(url, "first body", timestamp="2026-01-01T00:00:00.000000Z")
    loaded = store.latest(url)
    assert loaded is not None
    assert loaded.text == "first body"
    assert loaded.content_hash == content_hash("first body")
    assert loaded.url == url
    assert loaded.timestamp == snap.timestamp


def test_ordering_and_previous(tmp_path):
    store = SnapshotStore(tmp_path)
    url = "https://example.com/b"
    store.save(url, "v1", timestamp="2026-01-01T00:00:00.000000Z")
    store.save(url, "v2", timestamp="2026-01-02T00:00:00.000000Z")
    store.save(url, "v3", timestamp="2026-01-03T00:00:00.000000Z")
    snaps = store.list(url)
    assert [s.text for s in snaps] == ["v1", "v2", "v3"]
    assert store.latest(url).text == "v3"
    assert store.previous(url).text == "v2"
    assert store.count(url) == 3


def test_distinct_urls_are_isolated(tmp_path):
    store = SnapshotStore(tmp_path)
    store.save("https://example.com/x", "x-body")
    store.save("https://example.com/y", "y-body")
    assert store.count("https://example.com/x") == 1
    assert store.count("https://example.com/y") == 1
    assert store.latest("https://example.com/x").text == "x-body"


def test_missing_url_returns_empty(tmp_path):
    store = SnapshotStore(tmp_path)
    assert store.list("https://nope.example") == []
    assert store.latest("https://nope.example") is None
    assert store.previous("https://nope.example") is None
