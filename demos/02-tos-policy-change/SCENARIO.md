# Demo: SaaSCo - Terms of Service

A vendor's Terms of Service page. Legal and procurement teams watch these because a quiet edit can change data-retention windows or introduce a forced-arbitration / class-action waiver clause that affects your compliance posture and contractual exposure.

The baseline says data is deleted after 12 months and disputes go to the user's home courts. The updated version extends retention to 36 months (plus indefinite anonymized analytics) and inserts a binding-arbitration and class-action-waiver clause. Whitespace and the page font were also reflowed -- archivesnap ignores that and flags only the wording change.

> **Defensive, authorized-use monitoring only.** archivesnap watches pages you
> are entitled to watch (vendor advisories, your own status pages, policies you
> are party to). Respect each site's terms of service and `robots.txt`.

## Run it

```bash
# 1. Capture the baseline (the page as it stood before the change):
archivesnap snapshot "https://saasco.example/legal/terms" \
  --store demos/02-tos-policy-change/snaps --from-file demos/02-tos-policy-change/before.html

# 2. Watch the current version; emit SARIF for CI / code-scanning ingestion:
archivesnap watch demos/02-tos-policy-change/watch.config.json --once --format sarif

# Or get a non-zero exit code to gate a pipeline on a significant change:
archivesnap watch demos/02-tos-policy-change/watch.config.json --once --fail-on-change
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

Open the diff (`archivesnap diff "https://saasco.example/legal/terms" --store demos/02-tos-policy-change/snaps`), confirm the
wording change is the one described above, and route it to the owning team
(security, legal/privacy, SRE, or supply-chain) per your runbook. Then re-baseline
by leaving the new snapshot in place so the next change diffs against it.
