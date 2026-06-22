import json
from pathlib import Path

from archivesnap.cli import main

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def test_snapshot_diff_list_flow(tmp_path, capsys):
    store = str(tmp_path / "store")
    url = "https://acme.example/advisory"

    rc = main(["snapshot", url, "--store", store,
               "--from-file", str(EXAMPLES / "policy_v1.html")])
    assert rc == 0

    rc = main(["snapshot", url, "--store", store,
               "--from-file", str(EXAMPLES / "policy_v2.html")])
    assert rc == 0

    capsys.readouterr()
    rc = main(["diff", url, "--store", store, "--threshold", "0.05"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "diff:" in out
    assert "change" in out

    rc = main(["list", url, "--store", store])
    assert rc == 0
    assert "2 snapshot(s)" in capsys.readouterr().out


def test_snapshot_requires_source(tmp_path):
    rc = main(["snapshot", "https://x.example", "--store", str(tmp_path)])
    assert rc == 2


def test_diff_with_one_snapshot(tmp_path, capsys):
    store = str(tmp_path / "store")
    url = "https://acme.example/solo"
    main(["snapshot", url, "--store", store,
          "--from-file", str(EXAMPLES / "policy_v1.html")])
    capsys.readouterr()
    rc = main(["diff", url, "--store", store])
    assert rc == 0
    assert "nothing to diff" in capsys.readouterr().out


def test_watch_fail_on_change_gate(tmp_path, capsys):
    # Build a config whose store lives in tmp; baseline then change.
    store_dir = tmp_path / "store"
    cfg_path = tmp_path / "watch.json"
    url = "https://acme.example/advisory"

    cfg = {"store": str(store_dir), "threshold": 0.05,
           "pages": [{"url": url, "from_file": str(EXAMPLES / "policy_v1.html")}]}
    cfg_path.write_text(json.dumps(cfg), encoding="utf-8")

    # First pass: baseline, gate should pass (exit 0).
    rc = main(["watch", str(cfg_path), "--once", "--fail-on-change"])
    assert rc == 0

    # Point the same config at v2 and re-run: significant change -> exit 1.
    cfg["pages"][0]["from_file"] = str(EXAMPLES / "policy_v2.html")
    cfg_path.write_text(json.dumps(cfg), encoding="utf-8")
    capsys.readouterr()
    rc = main(["watch", str(cfg_path), "--once", "--fail-on-change"])
    assert rc == 1
    assert "significant change" in capsys.readouterr().out


def test_watch_without_fail_gate_exits_zero(tmp_path):
    store_dir = tmp_path / "store"
    cfg_path = tmp_path / "watch.json"
    url = "https://acme.example/advisory"
    cfg = {"store": str(store_dir), "threshold": 0.05,
           "pages": [{"url": url, "from_file": str(EXAMPLES / "policy_v2.html")}]}
    cfg_path.write_text(json.dumps(cfg), encoding="utf-8")
    assert main(["watch", str(cfg_path), "--once"]) == 0


def _two_pass_config(tmp_path):
    store_dir = tmp_path / "store"
    cfg_path = tmp_path / "watch.json"
    url = "https://acme.example/advisory"
    cfg = {"store": str(store_dir), "threshold": 0.05,
           "pages": [{"url": url, "from_file": str(EXAMPLES / "policy_v1.html")}]}
    cfg_path.write_text(json.dumps(cfg), encoding="utf-8")
    main(["watch", str(cfg_path), "--once"])  # baseline
    cfg["pages"][0]["from_file"] = str(EXAMPLES / "policy_v2.html")
    cfg_path.write_text(json.dumps(cfg), encoding="utf-8")
    return cfg_path


def test_watch_sarif_output_to_stdout(tmp_path, capsys):
    cfg_path = _two_pass_config(tmp_path)
    capsys.readouterr()
    rc = main(["watch", str(cfg_path), "--once", "--format", "sarif"])
    assert rc == 0
    log = json.loads(capsys.readouterr().out)
    assert log["version"] == "2.1.0"
    assert len(log["runs"][0]["results"]) == 1


def test_watch_json_output_to_file(tmp_path, capsys):
    cfg_path = _two_pass_config(tmp_path)
    out_path = tmp_path / "report.json"
    capsys.readouterr()
    rc = main(["watch", str(cfg_path), "--once", "--format", "json",
               "--output", str(out_path)])
    assert rc == 0
    assert "report written" in capsys.readouterr().out
    doc = json.loads(out_path.read_text(encoding="utf-8"))
    assert doc["any_significant"] is True
    assert doc["pages_changed"] == 1


def test_watch_sarif_with_fail_on_change_still_gates(tmp_path, capsys):
    cfg_path = _two_pass_config(tmp_path)
    capsys.readouterr()
    rc = main(["watch", str(cfg_path), "--once", "--format", "sarif",
               "--fail-on-change"])
    assert rc == 1
