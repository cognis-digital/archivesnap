# Demo: IoT Gateway - Firmware Release Notes

A device vendor's firmware release-notes page. Asset owners and OT/IoT security teams watch these so a new build that quietly fixes a privilege-escalation bug or disables a debug endpoint does not slip past the patch cycle.

The baseline (2.8.3) is a maintenance release with *no security-relevant changes*. The update (2.9.0) rotates the default device certificate chain, fixes a local privilege-escalation issue, and disables a legacy unauthenticated debug endpoint -- a clear escalation in patch priority.

> **Defensive, authorized-use monitoring only.** archivesnap watches pages you
> are entitled to watch (vendor advisories, your own status pages, policies you
> are party to). Respect each site's terms of service and `robots.txt`.

## Run it

```bash
# 1. Capture the baseline (the page as it stood before the change):
archivesnap snapshot "https://iotvendor.example/firmware/gateway/notes" \
  --store demos/05-firmware-release-notes/snaps --from-file demos/05-firmware-release-notes/before.html

# 2. Watch the current version; emit SARIF for CI / code-scanning ingestion:
archivesnap watch demos/05-firmware-release-notes/watch.config.json --once --format sarif

# Or get a non-zero exit code to gate a pipeline on a significant change:
archivesnap watch demos/05-firmware-release-notes/watch.config.json --once --fail-on-change
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

Open the diff (`archivesnap diff "https://iotvendor.example/firmware/gateway/notes" --store demos/05-firmware-release-notes/snaps`), confirm the
wording change is the one described above, and route it to the owning team
(security, legal/privacy, SRE, or supply-chain) per your runbook. Then re-baseline
by leaving the new snapshot in place so the next change diffs against it.
