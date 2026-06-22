"""archivesnap - web-page snapshot and change monitor.

Defensive monitoring tool: capture normalized snapshots of web pages,
store them locally, diff the latest against the previous, and report
meaningful changes while ignoring trivial whitespace noise.

Maintainer: Cognis Digital
License: COCL 1.0
"""

__version__ = "0.1.0"

from .normalize import html_to_text, normalize_text
from .hashing import content_hash
from .store import SnapshotStore, Snapshot
from .differ import diff_snapshots, DiffResult
from .fetcher import Fetcher, FileFetcher, LiveFetcher
from .report import to_json, to_sarif

__all__ = [
    "__version__",
    "html_to_text",
    "normalize_text",
    "content_hash",
    "SnapshotStore",
    "Snapshot",
    "diff_snapshots",
    "DiffResult",
    "Fetcher",
    "FileFetcher",
    "LiveFetcher",
    "to_json",
    "to_sarif",
]
