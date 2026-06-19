"""Content hashing helpers."""

from __future__ import annotations

import hashlib


def content_hash(text: str) -> str:
    """Return a stable SHA-256 hex digest of normalized text.

    Used as a fast equality check between snapshots so an unchanged page
    can be detected without computing a diff.
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
