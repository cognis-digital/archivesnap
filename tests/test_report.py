import json

from archivesnap.fetcher import MappingFetcher
from archivesnap.report import (
    RULE_MINOR,
    RULE_SIGNIFICANT,
    SARIF_VERSION,
    to_json,
    to_sarif,
)
from archivesnap.store import SnapshotStore
from archivesnap.watcher import run_watch

URL = "https://acme.example/advisory"
V1 = "<html><body><p>The portal is operating normally with no incidents.</p></body></html>"
V2 = "<html><body><p>The portal is down for emergency maintenance right now.</p></body></html>"


def _watch_twice(tmp_path, first, second, threshold=0.05):
    store = SnapshotStore(tmp_path)
    config = {"threshold": threshold, "pages": [{"url": URL}]}
    run_watch(config, fetcher=MappingFetcher({URL: first}), store=store)
    return run_watch(config, fetcher=MappingFetcher({URL: second}), store=store)


def test_sarif_significant_change_is_a_finding(tmp_path):
    result = _watch_twice(tmp_path, V1, V2)
    log = json.loads(to_sarif(result))

    assert log["version"] == SARIF_VERSION
    assert log["$schema"].endswith("sarif-schema-2.1.0.json")
    run = log["runs"][0]
    assert run["tool"]["driver"]["name"] == "archivesnap"
    rule_ids = {r["id"] for r in run["tool"]["driver"]["rules"]}
    assert {RULE_SIGNIFICANT, RULE_MINOR} <= rule_ids

    results = run["results"]
    assert len(results) == 1
    finding = results[0]
    assert finding["ruleId"] == RULE_SIGNIFICANT
    assert finding["level"] == "warning"
    assert finding["locations"][0]["physicalLocation"]["artifactLocation"]["uri"] == URL
    assert finding["properties"]["changeRatio"] > 0.05


def test_sarif_baseline_has_no_findings(tmp_path):
    store = SnapshotStore(tmp_path)
    config = {"threshold": 0.05, "pages": [{"url": URL}]}
    result = run_watch(config, fetcher=MappingFetcher({URL: V1}), store=store)
    log = json.loads(to_sarif(result))
    assert log["runs"][0]["results"] == []


def test_sarif_minor_change_excluded_unless_requested(tmp_path):
    # A one-character tweak across a long body keeps the ratio below threshold.
    long_a = "<html><body>" + "".join(
        f"<p>Stable status line number {i} unchanged.</p>" for i in range(40)
    ) + "</body></html>"
    long_b = long_a.replace("number 0 unchanged", "number 0 adjusted")
    result = _watch_twice(tmp_path, long_a, long_b, threshold=0.2)
    page = result.results[0]
    assert page.diff.changed is True
    assert page.diff.significant is False

    assert json.loads(to_sarif(result))["runs"][0]["results"] == []
    incl = json.loads(to_sarif(result, include_minor=True))["runs"][0]["results"]
    assert len(incl) == 1
    assert incl[0]["ruleId"] == RULE_MINOR
    assert incl[0]["level"] == "note"


def test_json_report_shape(tmp_path):
    result = _watch_twice(tmp_path, V1, V2)
    doc = json.loads(to_json(result))
    assert doc["tool"] == "archivesnap"
    assert doc["pages_total"] == 1
    assert doc["pages_changed"] == 1
    assert doc["any_significant"] is True
    page = doc["pages"][0]
    assert page["url"] == URL
    assert page["status"] == "changed"
    assert page["significant"] is True
    assert page["added_lines"] >= 1
