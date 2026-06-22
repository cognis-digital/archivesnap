# Demo: PaymentCo - Incident Report

A payment provider's per-incident status page as it transitions from *Investigating* to *Resolved* with a root-cause writeup. Teams that depend on the provider watch the incident page so they can update their own status, quantify customer impact, and capture the root cause for their records.

The baseline is the initial *Investigating* notice. The update is the *Resolved* state with the root cause (a misconfigured rate limiter), the exact rollback time, and a quantified impact (8 percent of authorizations failed for 45 minutes).

> **Defensive, authorized-use monitoring only.** archivesnap watches pages you
> are entitled to watch (vendor advisories, your own status pages, policies you
> are party to). Respect each site's terms of service and `robots.txt`.

## Run it

```bash
# 1. Capture the baseline (the page as it stood before the change):
archivesnap snapshot "https://status.paymentco.example/incidents/2026-06-21" \
  --store demos/09-incident-postmortem/snaps --from-file demos/09-incident-postmortem/before.html

# 2. Watch the current version; emit SARIF for CI / code-scanning ingestion:
archivesnap watch demos/09-incident-postmortem/watch.config.json --once --format sarif

# Or get a non-zero exit code to gate a pipeline on a significant change:
archivesnap watch demos/09-incident-postmortem/watch.config.json --once --fail-on-change
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

Open the diff (`archivesnap diff "https://status.paymentco.example/incidents/2026-06-21" --store demos/09-incident-postmortem/snaps`), confirm the
wording change is the one described above, and route it to the owning team
(security, legal/privacy, SRE, or supply-chain) per your runbook. Then re-baseline
by leaving the new snapshot in place so the next change diffs against it.
