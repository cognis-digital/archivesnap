# Demo: Vendor Widget Server - Known Issues Catalog

A vendor's own known-issues catalog page (the kind that mirrors a CISA-KEV-style "known exploited" list). Vulnerability-management teams watch these to catch the moment an item flips from *no known exploitation* to *actively exploited in the wild*, which changes patch urgency overnight.

The baseline lists two benign open items and states no exploitation has been observed. The update adds a new item (unauthenticated path to the admin API) **and** flips the exploitation note to *active exploitation in the wild*. Note: the issue identifiers here (WS-101..103) are illustrative placeholders, not real CVE IDs -- swap in your real source's page when you deploy this.

> **Defensive, authorized-use monitoring only.** archivesnap watches pages you
> are entitled to watch (vendor advisories, your own status pages, policies you
> are party to). Respect each site's terms of service and `robots.txt`.

## Run it

```bash
# 1. Capture the baseline (the page as it stood before the change):
archivesnap snapshot "https://vendor.example/kb/catalog/widget-server" \
  --store demos/04-kev-catalog-entry/snaps --from-file demos/04-kev-catalog-entry/before.html

# 2. Watch the current version; emit SARIF for CI / code-scanning ingestion:
archivesnap watch demos/04-kev-catalog-entry/watch.config.json --once --format sarif

# Or get a non-zero exit code to gate a pipeline on a significant change:
archivesnap watch demos/04-kev-catalog-entry/watch.config.json --once --fail-on-change
```

The watch config's `threshold` is `0.04`; the change below scores well
above it, so it registers as a **significant** change (a SARIF `warning`).

## What to expect

- The first `snapshot` stores a baseline; it prints the timestamp and content hash.
- The `watch --format sarif` run emits a SARIF 2.1.0 log with one `result`
  (rule `page-changed-significantly`, level `warning`) pointing at the URL,
  carrying the change ratio and added/removed line counts in `properties`.
- `--fail-on-change` exits non-zero, so a scheduler or CI job treats the change
  as an actionable signal.

## How to act

Open the diff (`archivesnap diff "https://vendor.example/kb/catalog/widget-server" --store demos/04-kev-catalog-entry/snaps`), confirm the
wording change is the one described above, and route it to the owning team
(security, legal/privacy, SRE, or supply-chain) per your runbook. Then re-baseline
by leaving the new snapshot in place so the next change diffs against it.
