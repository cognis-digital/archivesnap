# Demo: Package Registry - auth-helper listing

A public package-registry listing for a dependency you ship. Supply-chain defenders watch the listing page itself, because an unexpected new maintainer account, a changed repository link, or a surprise release can be the first visible sign of an account takeover or a malicious-release attempt.

The baseline shows a single verified maintainer org and the official repo link. The update shows a brand-new unverified individual maintainer added two days ago, a fresh release published by that account, and a repository link that now points at a different recently-created fork -- a textbook set of takeover red flags worth an immediate human review.

> **Defensive, authorized-use monitoring only.** archivesnap watches pages you
> are entitled to watch (vendor advisories, your own status pages, policies you
> are party to). Respect each site's terms of service and `robots.txt`.

## Run it

```bash
# 1. Capture the baseline (the page as it stood before the change):
archivesnap snapshot "https://registry.example/package/auth-helper" \
  --store demos/10-package-registry-listing/snaps --from-file demos/10-package-registry-listing/before.html

# 2. Watch the current version; emit SARIF for CI / code-scanning ingestion:
archivesnap watch demos/10-package-registry-listing/watch.config.json --once --format sarif

# Or get a non-zero exit code to gate a pipeline on a significant change:
archivesnap watch demos/10-package-registry-listing/watch.config.json --once --fail-on-change
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

Open the diff (`archivesnap diff "https://registry.example/package/auth-helper" --store demos/10-package-registry-listing/snaps`), confirm the
wording change is the one described above, and route it to the owning team
(security, legal/privacy, SRE, or supply-chain) per your runbook. Then re-baseline
by leaving the new snapshot in place so the next change diffs against it.
