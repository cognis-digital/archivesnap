"""Structured reporting for watch runs.

Turns a :class:`~archivesnap.watcher.WatchResult` into machine-readable
reports so a ``watch`` pass can feed CI dashboards and security tooling:

- ``to_json`` — a compact, stable JSON document describing every page.
- ``to_sarif`` — a SARIF 2.1.0 log where each *significant* page change is a
  ``result`` (finding). SARIF is the standard GitHub code-scanning ingests,
  so a scheduled archivesnap watch can surface monitored-page changes right
  in a repo's Security tab.

archivesnap is a defensive page-monitor: a "finding" here means *the wording
of a page you are authorized to watch changed enough to merit review* — e.g.
a vendor advisory, a policy page, or a status page. Nothing about exploiting
anything; the report just routes a content-change signal into standard rails.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from . import __version__

if TYPE_CHECKING:  # pragma: no cover
    from .watcher import WatchResult

SARIF_VERSION = "2.1.0"
SARIF_SCHEMA = (
    "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/"
    "Schemas/sarif-schema-2.1.0.json"
)
TOOL_INFO_URI = "https://github.com/cognis-digital/archivesnap"

# Stable rule ids surfaced in SARIF.
RULE_SIGNIFICANT = "page-changed-significantly"
RULE_MINOR = "page-changed-minor"


def _page_dict(result) -> dict:
    """Serialize a single :class:`PageResult` to a plain dict."""
    d: dict = {"url": result.url, "status": result.status}
    diff = result.diff
    if diff is not None:
        d["changed"] = diff.changed
        d["significant"] = diff.significant
        d["change_ratio"] = diff.change_ratio
        d["threshold"] = diff.threshold
        d["added_lines"] = diff.added_lines
        d["removed_lines"] = diff.removed_lines
    return d


def to_json(watch_result: "WatchResult", *, indent: int | None = 2) -> str:
    """Render a watch run as a stable JSON document."""
    pages = [_page_dict(r) for r in watch_result.results]
    doc = {
        "tool": "archivesnap",
        "version": __version__,
        "pages_total": len(watch_result.results),
        "pages_changed": len(watch_result.changed_pages),
        "any_significant": watch_result.any_significant,
        "pages": pages,
    }
    return json.dumps(doc, indent=indent, ensure_ascii=False, sort_keys=True)


def _sarif_level(result) -> str:
    """Map a page result onto a SARIF result level."""
    if result.diff is not None and result.diff.significant:
        return "warning"
    return "note"


def to_sarif(watch_result: "WatchResult", *,
             include_minor: bool = False, indent: int | None = 2) -> str:
    """Render a watch run as a SARIF 2.1.0 log.

    Every significant page change becomes a SARIF ``result``. Minor (non
    significant) changes are included only when ``include_minor`` is set;
    new-baseline and unchanged pages never produce findings.
    """
    rules = [
        {
            "id": RULE_SIGNIFICANT,
            "name": "PageChangedSignificantly",
            "shortDescription": {
                "text": "A monitored page changed above the significance "
                        "threshold.",
            },
            "fullDescription": {
                "text": "The normalized visible text of a monitored page "
                        "changed by a ratio at or above the configured "
                        "threshold since the previous snapshot.",
            },
            "defaultConfiguration": {"level": "warning"},
        },
        {
            "id": RULE_MINOR,
            "name": "PageChangedMinor",
            "shortDescription": {
                "text": "A monitored page changed below the significance "
                        "threshold.",
            },
            "defaultConfiguration": {"level": "note"},
        },
    ]

    results = []
    for r in watch_result.results:
        diff = r.diff
        if diff is None or not diff.changed:
            continue
        if not diff.significant and not include_minor:
            continue
        rule_id = RULE_SIGNIFICANT if diff.significant else RULE_MINOR
        verdict = "significantly" if diff.significant else "slightly"
        message = (
            f"Monitored page {r.url} changed {verdict} "
            f"(ratio={diff.change_ratio:.3f}, threshold={diff.threshold:.3f}, "
            f"+{diff.added_lines}/-{diff.removed_lines})."
        )
        results.append({
            "ruleId": rule_id,
            "level": _sarif_level(r),
            "message": {"text": message},
            "locations": [{
                "physicalLocation": {
                    "artifactLocation": {"uri": r.url},
                },
            }],
            "properties": {
                "changeRatio": diff.change_ratio,
                "threshold": diff.threshold,
                "addedLines": diff.added_lines,
                "removedLines": diff.removed_lines,
            },
        })

    log = {
        "version": SARIF_VERSION,
        "$schema": SARIF_SCHEMA,
        "runs": [{
            "tool": {
                "driver": {
                    "name": "archivesnap",
                    "informationUri": TOOL_INFO_URI,
                    "version": __version__,
                    "rules": rules,
                },
            },
            "results": results,
        }],
    }
    return json.dumps(log, indent=indent, ensure_ascii=False, sort_keys=True)
