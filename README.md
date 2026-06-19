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

## Development

```bash
PYTHONUTF8=1 python -m pytest      # Windows
python -m pytest                   # other platforms
```

Tests cover snapshot store/load, diffing and change-ratio scoring, the
significance threshold, the watch flow with a fake in-memory fetcher, and the
`--fail-on-change` exit gate. No test touches the network.

## Scope and intent

archivesnap is intended for **legitimate, defensive page monitoring** of
content you are entitled to watch. Respect each site's terms of service and
`robots.txt`, and rate-limit live fetches responsibly.
