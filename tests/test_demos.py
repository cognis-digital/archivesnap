"""Every shipped demo must actually fire: a significant change with one finding."""
import json
from pathlib import Path

import pytest

from archivesnap.fetcher import FileFetcher
from archivesnap.normalize import html_to_text
from archivesnap.report import to_sarif
from archivesnap.store import SnapshotStore
from archivesnap.watcher import load_config, run_watch

DEMOS = Path(__file__).resolve().parent.parent / "demos"


def _demo_dirs():
    return sorted(p for p in DEMOS.iterdir() if p.is_dir())


def test_demos_are_present():
    dirs = _demo_dirs()
    assert len(dirs) >= 5
    for d in dirs:
        assert (d / "before.html").is_file()
        assert (d / "after.html").is_file()
        assert (d / "watch.config.json").is_file()
        assert (d / "SCENARIO.md").is_file()


@pytest.mark.parametrize("demo", _demo_dirs(), ids=lambda p: p.name)
def test_demo_fires_significant_change(demo, tmp_path):
    cfg = load_config(demo / "watch.config.json")
    threshold = float(cfg.get("threshold", 0.05))
    url = cfg["pages"][0]["url"]
    assert cfg["pages"][0]["from_file"] == "after.html"

    store = SnapshotStore(tmp_path)
    baseline = html_to_text((demo / "before.html").read_text(encoding="utf-8"))
    store.save(url, baseline, meta={"source": "before"})

    result = run_watch(
        {"threshold": threshold, "pages": [{"url": url}]},
        fetcher=FileFetcher(demo / "after.html"),
        store=store,
    )
    page = result.results[0]
    assert page.status == "changed"
    assert page.significant is True

    findings = json.loads(to_sarif(result))["runs"][0]["results"]
    assert len(findings) == 1
    assert findings[0]["ruleId"] == "page-changed-significantly"
