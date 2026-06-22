from archivesnap.store import SnapshotStore


def test_same_timestamp_saves_do_not_collide(tmp_path):
    """Two captures sharing one timestamp string must both persist and order."""
    store = SnapshotStore(tmp_path)
    url = "https://example.com/fast"
    ts = "2026-06-22T00:00:00.000000Z"

    a = store.save(url, "first", timestamp=ts)
    b = store.save(url, "second", timestamp=ts)
    c = store.save(url, "third", timestamp=ts)

    # Distinct sequence numbers guarantee distinct filenames.
    assert a.seq < b.seq < c.seq

    snaps = store.list(url)
    assert store.count(url) == 3
    assert [s.text for s in snaps] == ["first", "second", "third"]
    assert store.latest(url).text == "third"
    assert store.previous(url).text == "second"


def test_seq_persists_across_reload(tmp_path):
    store = SnapshotStore(tmp_path)
    url = "https://example.com/persist"
    store.save(url, "a", timestamp="2026-06-22T00:00:00.000000Z")
    store.save(url, "b", timestamp="2026-06-22T00:00:00.000000Z")

    reopened = SnapshotStore(tmp_path)
    snaps = reopened.list(url)
    assert [s.text for s in snaps] == ["a", "b"]
    assert all(s.seq > 0 for s in snaps)


def test_legacy_snapshot_without_seq_still_loads(tmp_path):
    """Snapshots written before the seq field default to seq=0 and still load."""
    store = SnapshotStore(tmp_path)
    url = "https://example.com/legacy"
    target = store._dir_for(url)
    target.mkdir(parents=True, exist_ok=True)
    legacy = (
        '{\n'
        '  "url": "https://example.com/legacy",\n'
        '  "timestamp": "2026-01-01T00:00:00.000000Z",\n'
        '  "content_hash": "deadbeef",\n'
        '  "text": "legacy body",\n'
        '  "meta": {}\n'
        '}\n'
    )
    (target / "legacy.json").write_text(legacy, encoding="utf-8")

    snaps = store.list(url)
    assert len(snaps) == 1
    assert snaps[0].text == "legacy body"
    assert snaps[0].seq == 0
