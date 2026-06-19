"""Pluggable page fetchers.

Network access is abstracted behind the :class:`Fetcher` protocol so the
tool runs fully offline in tests (via :class:`FileFetcher`) and uses
``urllib`` only on the explicit ``--live`` path (:class:`LiveFetcher`).
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol


class Fetcher(Protocol):
    """Anything that can return the raw body for a URL."""

    def fetch(self, url: str) -> str:  # pragma: no cover - protocol
        ...


class FileFetcher:
    """Return page content from a local file instead of the network.

    Used for offline snapshots (``--from-file``) and for tests. The same
    ``path`` is returned for every URL, which suits single-page captures.
    """

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def fetch(self, url: str) -> str:
        return self.path.read_text(encoding="utf-8")


class MappingFetcher:
    """Return content from an in-memory ``{url: html}`` mapping.

    Convenient for ``watch`` tests and for driving multiple pages without
    touching the filesystem or network.
    """

    def __init__(self, mapping: dict[str, str]):
        self.mapping = dict(mapping)

    def fetch(self, url: str) -> str:
        if url not in self.mapping:
            raise KeyError(f"no content mapped for url: {url}")
        return self.mapping[url]


class LiveFetcher:
    """Fetch over HTTP(S) using the standard library ``urllib``.

    Only reached on the explicit ``--live`` path; never used in tests.
    """

    def __init__(self, timeout: float = 30.0, user_agent: str = "archivesnap/0.1"):
        self.timeout = timeout
        self.user_agent = user_agent

    def fetch(self, url: str) -> str:  # pragma: no cover - network path
        import urllib.request

        req = urllib.request.Request(url, headers={"User-Agent": self.user_agent})
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            charset = resp.headers.get_content_charset() or "utf-8"
            return resp.read().decode(charset, errors="replace")
