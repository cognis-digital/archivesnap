# Demo: DB Engine - Lifecycle Policy

A vendor product-lifecycle / end-of-life policy page. Platform and infrastructure teams watch these so an EOL date appears on the roadmap the moment it is announced -- running an unsupported, no-more-security-fixes version is a slow-burning risk.

The baseline says nothing is scheduled for EOL and 5.x has full support. The update downgrades 5.x to *security fixes only* and sets a hard EOL date of 2026-12-31, with a directive to migrate to 6.x.

> **Defensive, authorized-use monitoring only.** archivesnap watches pages you
> are entitled to watch (vendor advisories, your own status pages, policies you
> are party to). Respect each site's terms of service and `robots.txt`.

## Run it

```bash
# 1. Capture the baseline (the page as it stood before the change):
archivesnap snapshot "https://vendor.example/lifecycle/db-engine" \
  --store demos/08-product-eol-notice/snaps --from-file demos/08-product-eol-notice/before.html

# 2. Watch the current version; emit SARIF for CI / code-scanning ingestion:
archivesnap watch demos/08-product-eol-notice/watch.config.json --once --format sarif

# Or get a non-zero exit code to gate a pipeline on a significant change:
archivesnap watch demos/08-product-eol-notice/watch.config.json --once --fail-on-change
```

The watch config's `threshold` is `0.05`; the change below scores well
above it, so it registers as a **significant** change (a SARIF `warning`).

## What to expect

- The first `snapshot` stores a baseline; it prints the timestamp and content hash.
- The `watch --format sarif` run emits a SARIF 2.1.0 log with one `result`
  (rule `page-changed-significantly`, level `warning`) pointing at the URL,
  carrying the change ratio and added/removed line counts in `properties`.
- `--fail-on-change` exits non-zero, so a scheduler or CI job treats the change
  as an actionable signal.

## How to act

Open the diff (`archivesnap diff "https://vendor.example/lifecycle/db-engine" --store demos/08-product-eol-notice/snaps`), confirm the
wording change is the one described above, and route it to the owning team
(security, legal/privacy, SRE, or supply-chain) per your runbook. Then re-baseline
by leaving the new snapshot in place so the next change diffs against it.
