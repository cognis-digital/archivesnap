from archivesnap.fetcher import MappingFetcher
from archivesnap.store import SnapshotStore
from archivesnap.watcher import run_watch

URL = "https://acme.example/advisory"
HTML_V1 = "<html><body><p>The portal is operating normally.</p></body></html>"
HTML_V2 = "<html><body><p>The portal is down for emergency maintenance.</p></body></html>"


def test_first_pass_is_baseline(tmp_path):
    store = SnapshotStore(tmp_path)
    fetcher = MappingFetcher({URL: HTML_V1})
    config = {"threshold": 0.05, "pages": [{"url": URL}]}
    result = run_watch(config, fetcher=fetcher, store=store)
    assert result.results[0].status == "new"
    assert result.any_significant is False


def test_second_pass_detects_significant_change(tmp_path):
    store = SnapshotStore(tmp_path)
    config = {"threshold": 0.05, "pages": [{"url": URL}]}

    run_watch(config, fetcher=MappingFetcher({URL: HTML_V1}), store=store)
    result = run_watch(config, fetcher=MappingFetcher({URL: HTML_V2}), store=store)

    page = result.results[0]
    assert page.status == "changed"
    assert page.significant is True
    assert result.any_significant is True
    assert len(result.changed_pages) == 1


def test_unchanged_page_not_flagged(tmp_path):
    store = SnapshotStore(tmp_path)
    config = {"threshold": 0.05, "pages": [{"url": URL}]}
    run_watch(config, fetcher=MappingFetcher({URL: HTML_V1}), store=store)
    # Same content but reflowed whitespace/markup -> normalized identical.
    reflowed = "<html><body>\n  <p>The   portal is operating normally.</p>\n</body></html>"
    result = run_watch(config, fetcher=MappingFetcher({URL: reflowed}), store=store)
    assert result.results[0].status == "unchanged"
    assert result.any_significant is False
