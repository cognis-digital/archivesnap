"""Diffing and change-significance scoring."""

from __future__ import annotations

import difflib
from dataclasses import dataclass

from .store import Snapshot


@dataclass
class DiffResult:
    """Outcome of comparing two snapshots."""

    changed: bool             # hashes differ at all
    change_ratio: float       # 0.0 (identical) .. 1.0 (completely different)
    significant: bool         # change_ratio >= threshold
    threshold: float
    unified: str              # unified diff text
    added_lines: int
    removed_lines: int

    def summary(self) -> str:
        if not self.changed:
            return "no change"
        verdict = "SIGNIFICANT" if self.significant else "minor"
        return (
            f"{verdict} change "
            f"(ratio={self.change_ratio:.3f}, threshold={self.threshold:.3f}, "
            f"+{self.added_lines}/-{self.removed_lines})"
        )


def change_ratio(old_text: str, new_text: str) -> float:
    """Fraction of content that changed, in ``[0.0, 1.0]``.

    Derived from :class:`difflib.SequenceMatcher` line-level similarity:
    ``1 - ratio``. Identical text yields ``0.0``.
    """
    old_lines = old_text.split("\n")
    new_lines = new_text.split("\n")
    matcher = difflib.SequenceMatcher(a=old_lines, b=new_lines, autojunk=False)
    return round(1.0 - matcher.ratio(), 6)


def _count_changes(old_lines: list[str], new_lines: list[str]) -> tuple[int, int]:
    added = removed = 0
    matcher = difflib.SequenceMatcher(a=old_lines, b=new_lines, autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag in ("replace", "delete"):
            removed += i2 - i1
        if tag in ("replace", "insert"):
            added += j2 - j1
    return added, removed


def diff_text(old_text: str, new_text: str, *, threshold: float = 0.05,
              old_label: str = "previous", new_label: str = "latest") -> DiffResult:
    """Compare two normalized text bodies and score the change."""
    old_lines = old_text.split("\n")
    new_lines = new_text.split("\n")
    unified = "\n".join(
        difflib.unified_diff(
            old_lines, new_lines,
            fromfile=old_label, tofile=new_label, lineterm="",
        )
    )
    ratio = change_ratio(old_text, new_text)
    added, removed = _count_changes(old_lines, new_lines)
    changed = old_text != new_text
    return DiffResult(
        changed=changed,
        change_ratio=ratio,
        significant=changed and ratio >= threshold,
        threshold=threshold,
        unified=unified,
        added_lines=added,
        removed_lines=removed,
    )


def diff_snapshots(old: Snapshot, new: Snapshot, *,
                   threshold: float = 0.05) -> DiffResult:
    """Compare two snapshots, short-circuiting on equal content hashes."""
    if old.content_hash == new.content_hash:
        return DiffResult(
            changed=False, change_ratio=0.0, significant=False,
            threshold=threshold, unified="", added_lines=0, removed_lines=0,
        )
    return diff_text(
        old.text, new.text, threshold=threshold,
        old_label=old.timestamp, new_label=new.timestamp,
    )
