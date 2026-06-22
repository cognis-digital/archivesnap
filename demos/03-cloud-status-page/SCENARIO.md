# Demo: CloudCo - Service Status

A managed-cloud provider status page. SRE / on-call teams watch upstream status pages so they learn about provider-side degradation before their own alerts cascade.

The baseline shows everything Operational. The updated version flips Object Storage to *Degraded performance* (elevated PUT errors in us-east) and Identity to *Partial outage* (delayed token issuance). A `--fail-on-change` watch on a 5-minute scheduler turns this into an early upstream-incident signal.

> **Defensive, authorized-use monitoring only.** archivesnap watches pages you
> are entitled to watch (vendor advisories, your own status pages, policies you
> are party to). Respect each site's terms of service and `robots.txt`.

## Run it

```bash
# 1. Capture the baseline (the page as it stood before the change):
archivesnap snapshot "https://status.cloudco.example/" \
  --store demos/03-cloud-status-page/snaps --from-file demos/03-cloud-status-page/before.html

# 2. Watch the current version; emit SARIF for CI / code-scanning ingestion:
archivesnap watch demos/03-cloud-status-page/watch.config.json --once --format sarif

# Or get a non-zero exit code to gate a pipeline on a significant change:
archivesnap watch demos/03-cloud-status-page/watch.config.json --once --fail-on-change
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

Open the diff (`archivesnap diff "https://status.cloudco.example/" --store demos/03-cloud-status-page/snaps`), confirm the
wording change is the one described above, and route it to the owning team
(security, legal/privacy, SRE, or supply-chain) per your runbook. Then re-baseline
by leaving the new snapshot in place so the next change diffs against it.
