# Demo: App Vendor - Subprocessor List

A processor's published subprocessor list (a GDPR / DPA staple). Privacy and vendor-risk teams must be notified when a new subprocessor is added or a data-transfer region changes, because both can trigger DPA obligations and customer notifications.

The baseline lists two EU subprocessors and states all data stays in the EU. The update adds a **US** analytics subprocessor and acknowledges a new cross-border transfer under standard contractual clauses -- exactly the kind of change a compliance team must catch the day it lands.

> **Defensive, authorized-use monitoring only.** archivesnap watches pages you
> are entitled to watch (vendor advisories, your own status pages, policies you
> are party to). Respect each site's terms of service and `robots.txt`.

## Run it

```bash
# 1. Capture the baseline (the page as it stood before the change):
archivesnap snapshot "https://app.example/legal/subprocessors" \
  --store demos/07-privacy-policy-subprocessors/snaps --from-file demos/07-privacy-policy-subprocessors/before.html

# 2. Watch the current version; emit SARIF for CI / code-scanning ingestion:
archivesnap watch demos/07-privacy-policy-subprocessors/watch.config.json --once --format sarif

# Or get a non-zero exit code to gate a pipeline on a significant change:
archivesnap watch demos/07-privacy-policy-subprocessors/watch.config.json --once --fail-on-change
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

Open the diff (`archivesnap diff "https://app.example/legal/subprocessors" --store demos/07-privacy-policy-subprocessors/snaps`), confirm the
wording change is the one described above, and route it to the owning team
(security, legal/privacy, SRE, or supply-chain) per your runbook. Then re-baseline
by leaving the new snapshot in place so the next change diffs against it.
