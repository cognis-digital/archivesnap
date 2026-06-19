"""Local snapshot store.

Snapshots for a given URL are kept in a per-URL directory under the store
root. Each snapshot is a JSON file named by capture timestamp, holding the
normalized text, its content hash, the source URL, and metadata.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path

from .hashing import content_hash


@dataclass
class Snapshot:
    """A single captured snapshot of a page."""

    url: str
    timestamp: str            # ISO-8601 UTC
    content_hash: str
    text: str
    meta: dict

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, ensure_ascii=False, sort_keys=True)

    @classmethod
    def from_dict(cls, data: dict) -> "Snapshot":
        return cls(
            url=data["url"],
            timestamp=data["timestamp"],
            content_hash=data["content_hash"],
            text=data["text"],
            meta=data.get("meta", {}),
        )


def _url_key(url: str) -> str:
    """Map a URL to a filesystem-safe directory name.

    A short hash prefix guarantees uniqueness while a slug keeps it readable.
    """
    slug = re.sub(r"[^A-Za-z0-9._-]+", "_", url).strip("_")[:60]
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:12]
    return f"{slug}-{digest}" if slug else digest


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


class SnapshotStore:
    """Filesystem-backed store of page snapshots."""

    def __init__(self, root: str | Path):
        self.root = Path(root)

    def _dir_for(self, url: str) -> Path:
        return self.root / _url_key(url)

    def save(self, url: str, text: str, meta: dict | None = None,
             timestamp: str | None = None) -> Snapshot:
        """Persist a snapshot of ``text`` for ``url`` and return it."""
        ts = timestamp or _utc_now_iso()
        snap = Snapshot(
            url=url,
            timestamp=ts,
            content_hash=content_hash(text),
            text=text,
            meta=meta or {},
        )
        target_dir = self._dir_for(url)
        target_dir.mkdir(parents=True, exist_ok=True)
        # File name is timestamp-derived; sanitize ':' and '.' for portability.
        fname = re.sub(r"[^0-9A-Za-z]", "", ts) + ".json"
        (target_dir / fname).write_text(snap.to_json(), encoding="utf-8")
        return snap

    def list(self, url: str) -> list[Snapshot]:
        """Return all snapshots for ``url`` ordered oldest -> newest."""
        target_dir = self._dir_for(url)
        if not target_dir.is_dir():
            return []
        snaps = []
        for path in target_dir.glob("*.json"):
            data = json.loads(path.read_text(encoding="utf-8"))
            snaps.append(Snapshot.from_dict(data))
        snaps.sort(key=lambda s: s.timestamp)
        return snaps

    def latest(self, url: str) -> Snapshot | None:
        snaps = self.list(url)
        return snaps[-1] if snaps else None

    def previous(self, url: str) -> Snapshot | None:
        """Second-newest snapshot, or ``None`` if fewer than two exist."""
        snaps = self.list(url)
        return snaps[-2] if len(snaps) >= 2 else None

    def count(self, url: str) -> int:
        return len(self.list(url))
