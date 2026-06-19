"""Watch-list orchestration.

A watch config is JSON of the form::

    {
      "store": "snapshots",
      "threshold": 0.05,
      "pages": [
        {"url": "https://example.com/policy", "from_file": "examples/policy_v2.html"}
      ]
    }

For each page, the current content is fetched, normalized, snapshotted, and
diffed against the prior snapshot. The result lists which pages changed
significantly.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .differ import diff_snapshots, DiffResult
from .fetcher import Fetcher, FileFetcher
from .normalize import html_to_text
from .store import SnapshotStore


@dataclass
class PageResult:
    url: str
    status: str               # "new" | "unchanged" | "changed"
    diff: DiffResult | None

    @property
    def significant(self) -> bool:
        return self.diff is not None and self.diff.significant


@dataclass
class WatchResult:
    results: list[PageResult]

    @property
    def any_significant(self) -> bool:
        return any(r.significant for r in self.results)

    @property
    def changed_pages(self) -> list[PageResult]:
        return [r for r in self.results if r.significant]


def load_config(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def run_watch(config: dict, *, base_dir: str | Path = ".",
              fetcher: Fetcher | None = None,
              store: SnapshotStore | None = None) -> WatchResult:
    """Process every page in ``config`` once.

    ``fetcher`` (and ``store``), when supplied, override the config-driven
    defaults; this is what lets tests run with a fake fetcher and no network.
    Relative ``from_file`` / ``store`` paths resolve against ``base_dir``
    (normally the directory holding the config file).
    """
    base = Path(base_dir)
    threshold = float(config.get("threshold", 0.05))
    if store is None:
        store_dir = config.get("store", "snapshots")
        store = SnapshotStore(base / store_dir)

    results: list[PageResult] = []
    for page in config.get("pages", []):
        url = page["url"]

        if fetcher is not None:
            page_fetcher: Fetcher = fetcher
        elif page.get("from_file"):
            page_fetcher = FileFetcher(base / page["from_file"])
        else:
            raise ValueError(
                f"page {url!r} has no 'from_file' and no fetcher supplied "
                "(use --live or provide from_file)"
            )

        text = html_to_text(page_fetcher.fetch(url))
        prev = store.latest(url)
        new_snap = store.save(url, text, meta={"source": "watch"})

        if prev is None:
            results.append(PageResult(url=url, status="new", diff=None))
            continue

        diff = diff_snapshots(prev, new_snap, threshold=threshold)
        status = "changed" if diff.changed else "unchanged"
        results.append(PageResult(url=url, status=status, diff=diff))

    return WatchResult(results=results)
