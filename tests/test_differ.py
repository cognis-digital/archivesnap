from archivesnap.differ import diff_text, diff_snapshots, change_ratio
from archivesnap.store import Snapshot
from archivesnap.hashing import content_hash


def _snap(text, ts="2026-01-01T00:00:00.000000Z"):
    return Snapshot(url="u", timestamp=ts, content_hash=content_hash(text),
                    text=text, meta={})


def test_identical_text_no_change():
    r = diff_text("same\ncontent", "same\ncontent")
    assert r.changed is False
    assert r.change_ratio == 0.0
    assert r.significant is False
    assert r.unified == ""


def test_small_change_below_threshold_is_minor():
    old = "\n".join(f"line {i}" for i in range(100))
    new = old.replace("line 50", "line 50 edited")
    r = diff_text(old, new, threshold=0.05)
    assert r.changed is True
    assert 0.0 < r.change_ratio < 0.05
    assert r.significant is False


def test_large_change_above_threshold_is_significant():
    old = "\n".join(f"line {i}" for i in range(20))
    new = "\n".join(f"different {i}" for i in range(20))
    r = diff_text(old, new, threshold=0.05)
    assert r.changed is True
    assert r.change_ratio > 0.05
    assert r.significant is True
    assert r.added_lines > 0 and r.removed_lines > 0


def test_change_ratio_bounds():
    assert change_ratio("a", "a") == 0.0
    assert change_ratio("a\nb\nc", "x\ny\nz") == 1.0


def test_diff_snapshots_hash_shortcircuit():
    a = _snap("body text", ts="2026-01-01T00:00:00.000000Z")
    b = _snap("body text", ts="2026-01-02T00:00:00.000000Z")
    r = diff_snapshots(a, b)
    assert r.changed is False
    assert r.unified == ""


def test_diff_snapshots_uses_timestamps_as_labels():
    a = _snap("old", ts="2026-01-01T00:00:00.000000Z")
    b = _snap("new", ts="2026-01-02T00:00:00.000000Z")
    r = diff_snapshots(a, b, threshold=0.01)
    assert r.changed is True
    assert "2026-01-01T00:00:00.000000Z" in r.unified
    assert "2026-01-02T00:00:00.000000Z" in r.unified
