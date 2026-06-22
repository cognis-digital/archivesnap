# Demo: Package Repository - Signing Keys

A package repository's signing-key page. Anyone who pins or verifies package signatures must watch this: a key rotation or revocation means your build pipeline's trusted keyring is now stale, and continuing to trust the old key is a supply-chain risk.

The baseline advertises RELEASE-2025 as the active key. The update rotates to RELEASE-2026 **and revokes** RELEASE-2025, instructing you to drop the old key and re-verify recent downloads. The key IDs here are illustrative labels, not real fingerprints -- point this at your real repo's page in production.

> **Defensive, authorized-use monitoring only.** archivesnap watches pages you
> are entitled to watch (vendor advisories, your own status pages, policies you
> are party to). Respect each site's terms of service and `robots.txt`.

## Run it

```bash
# 1. Capture the baseline (the page as it stood before the change):
archivesnap snapshot "https://pkg.example/security/signing-keys" \
  --store demos/06-signing-key-rotation/snaps --from-file demos/06-signing-key-rotation/before.html

# 2. Watch the current version; emit SARIF for CI / code-scanning ingestion:
archivesnap watch demos/06-signing-key-rotation/watch.config.json --once --format sarif

# Or get a non-zero exit code to gate a pipeline on a significant change:
archivesnap watch demos/06-signing-key-rotation/watch.config.json --once --fail-on-change
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

Open the diff (`archivesnap diff "https://pkg.example/security/signing-keys" --store demos/06-signing-key-rotation/snaps`), confirm the
wording change is the one described above, and route it to the owning team
(security, legal/privacy, SRE, or supply-chain) per your runbook. Then re-baseline
by leaving the new snapshot in place so the next change diffs against it.
