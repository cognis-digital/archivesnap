# archivesnap

**Web-page snapshot and change monitor.** Capture a normalized snapshot of a
page (visible text + content hash + timestamp), store snapshots locally, diff
the latest against the previous, and report *meaningful* changes while
ignoring trivial whitespace/markup noise.

archivesnap is built for **defensive monitoring** — keeping an eye on advisory
pages, policy pages, status pages, terms-of-service updates, and similar
content where you want to know when the wording actually changes. It is not a
scraper for bulk extraction; network access is opt-in.

- Standard library only. No third-party runtime dependencies.
- Python 3.10+.
- Network is abstracted behind an injectable fetcher, so it runs fully offline
  in tests and from local files. A `--live` flag uses `urllib` for real fetches.

License: COCL 1.0
Maintainer: Cognis Digital

---

## Install

```bash
pip install -e ".[dev]"   # dev extras add pytest
```

This installs the `archivesnap` console command.

## How it works

1. **Normalize.** HTML is reduced to visible text: `script`/`style`/`head`
   content is dropped, tags are removed, entities decoded, and whitespace
   collapsed into a stable canonical form. Two captures that differ only in
   markup or reflowed whitespace normalize to identical text.
2. **Hash.** The normalized text gets a SHA-256 content hash for fast
   equality checks.
3. **Store.** Each snapshot is a JSON file under a per-URL directory in the
   store root, named by capture timestamp.
4. **Diff.** The latest snapshot is compared to the previous one with
   `difflib`. A **change ratio** in `[0, 1]` scores how much changed; a
   configurable **threshold** decides whether the change is *significant*.

## Commands

### snapshot

Capture and store a snapshot. Offline by default — point it at a local file:

```bash
archivesnap snapshot https://acme.example/advisory \
  --store snapshots --from-file examples/policy_v1.html
```

Fetch live over the network instead:

```bash
archivesnap snapshot https://acme.example/advisory --store snapshots --live
```

### diff

Compare the latest snapshot to the previous one:

```bash
archivesnap diff https://acme.example/advisory --store snapshots --threshold 0.05
```

Prints the unified diff, the change ratio, the line add/remove counts, and a
significance verdict.

### list

List stored snapshots for a URL (oldest to newest), with timestamps and short
hashes:

```bash
archivesnap list https://acme.example/advisory --store snapshots
```

### watch

Check a list of pages from a JSON config in a single pass:

```bash
archivesnap watch examples/watch.config.json --once
```

Add `--fail-on-change` to make the process exit non-zero when any page changed
significantly — handy as a CI/scheduler gate:

```bash
archivesnap watch examples/watch.config.json --once --fail-on-change
```

Add `--live` to fetch every page over the network instead of from files.

#### Structured reports (JSON / SARIF)

A `watch` pass can emit a machine-readable report instead of the human text,
so it slots into CI dashboards and security tooling:

```bash
# Stable JSON summary of every page:
archivesnap watch examples/watch.config.json --once --format json

# SARIF 2.1.0 log — each *significant* change is a finding (rule
# `page-changed-significantly`, level `warning`). This is the format GitHub
# code scanning ingests, so a scheduled watch surfaces monitored-page changes
# right in a repo's Security tab:
archivesnap watch examples/watch.config.json --once --format sarif --output watch.sarif
```

`--format` accepts `text` (default), `json`, or `sarif`. `--output / -o` writes
the report to a file instead of stdout. `--fail-on-change` still applies, so you
can produce a SARIF artifact *and* fail the job on a significant change in one
pass. New-baseline and unchanged pages never produce findings.

#### Watch config format

```json
{
  "store": "snapshots",
  "threshold": 0.05,
  "pages": [
    { "url": "https://acme.example/advisory", "from_file": "policy_v2.html" }
  ]
}
```

Relative `store` and `from_file` paths resolve against the directory holding
the config file. Omit `from_file` and pass `--live` to fetch over the network.

## Quick offline demo

```bash
# Baseline, then a changed version, then diff:
archivesnap snapshot https://acme.example/advisory --store /tmp/snaps --from-file examples/policy_v1.html
archivesnap snapshot https://acme.example/advisory --store /tmp/snaps --from-file examples/policy_v2.html
archivesnap diff     https://acme.example/advisory --store /tmp/snaps
```

The example fixtures change support hours (6 PM -> 8 PM), the portal status
(normal -> scheduled maintenance), and the contact note — a significant change
that registers above the default threshold, even though markup and whitespace
were also reflowed between versions.

## Examples directory

- `examples/policy_v1.html` — baseline advisory page.
- `examples/policy_v2.html` — updated advisory (and reflowed markup).
- `examples/watch.config.json` — a one-page watch config.

## Real-use-case demos

The `demos/` directory holds ten self-contained, runnable scenarios. Each is a
folder with a `before.html` baseline, an `after.html` (the changed page in the
tool's real HTML input format), a `watch.config.json`, and a `SCENARIO.md` that
explains where the data comes from, what to expect, the exact run commands, and
how to act. Every demo is exercised by the test suite to prove it actually fires
a significant change.

| Demo | Defensive use case |
| --- | --- |
| `01-vendor-security-advisory` | Advisory escalates from *under investigation* to High severity + patch available |
| `02-tos-policy-change` | Terms of Service quietly extends data retention and adds forced arbitration |
| `03-cloud-status-page` | Upstream provider flips services to *Degraded* / *Partial outage* |
| `04-kev-catalog-entry` | Known-issue list flips an item to *actively exploited in the wild* |
| `05-firmware-release-notes` | Firmware build silently fixes a privilege-escalation bug |
| `06-signing-key-rotation` | Package signing key rotated **and** the old key revoked |
| `07-privacy-policy-subprocessors` | A new US subprocessor + cross-border data transfer appears |
| `08-product-eol-notice` | A supported version is given a hard end-of-life date |
| `09-incident-postmortem` | Incident page moves to *Resolved* with a root-cause writeup |
| `10-package-registry-listing` | A dependency listing shows account-takeover red flags |

```bash
# Run any demo: capture the baseline, then watch the changed page as SARIF.
archivesnap snapshot "https://acme.example/security/ACME-SA-2026-014" \
  --store demos/01-vendor-security-advisory/snaps \
  --from-file demos/01-vendor-security-advisory/before.html
archivesnap watch demos/01-vendor-security-advisory/watch.config.json --once --format sarif
```

The issue identifiers, key labels, and account names in the demos are
illustrative placeholders, not real CVE IDs / fingerprints — point each watch
config at your real source page when you deploy it.

## Development

```bash
PYTHONUTF8=1 python -m pytest      # Windows
python -m pytest                   # other platforms
```

Tests cover snapshot store/load, capture-order tie-breaking when timestamps
collide, diffing and change-ratio scoring, the significance threshold, the watch
flow with a fake in-memory fetcher, the `--fail-on-change` exit gate, the
JSON/SARIF reports, and an integration test that runs every shipped demo. No
test touches the network.

## Scope and intent

archivesnap is intended for **legitimate, defensive page monitoring** of
content you are entitled to watch. Respect each site's terms of service and
`robots.txt`, and rate-limit live fetches responsibly.
