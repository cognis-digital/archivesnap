# Demo: Acme Appliance - Security Advisory

A vendor security advisory page that evolves as the vendor learns more. Security
and patch-management teams watch advisory pages so they catch the exact moment an
advisory goes from *under investigation, no patch* to *High severity, patch
available* -- the transition that should trigger an emergency patch cycle.

The baseline says the issue is *Under investigation* with *no patch available*
and only a network-restriction workaround. The updated version names the issue
class (authentication bypass on releases 4.2-4.5), raises severity to **High**,
and announces fixed versions 4.5.1 / 4.6.0 are available -- while also reflowing
the page markup and font (which archivesnap ignores).

> **Defensive, authorized-use monitoring only.** archivesnap watches pages you
> are entitled to watch (vendor advisories, your own status pages, policies you
> are party to). Respect each site's terms of service and `robots.txt`.

## Run it

```bash
# 1. Capture the baseline (the advisory as it stood while under investigation):
archivesnap snapshot "https://acme.example/security/ACME-SA-2026-014" \
  --store demos/01-vendor-security-advisory/snaps \
  --from-file demos/01-vendor-security-advisory/before.html

# 2. Watch the current version; emit SARIF for CI / code-scanning ingestion:
archivesnap watch demos/01-vendor-security-advisory/watch.config.json --once --format sarif

# Or get a non-zero exit code to gate a pipeline on a significant change:
archivesnap watch demos/01-vendor-security-advisory/watch.config.json --once --fail-on-change
```

The watch config's `threshold` is `0.05`; the change above scores well above it,
so it registers as a **significant** change (a SARIF `warning`).

## What to expect

- The first `snapshot` stores a baseline; it prints the timestamp and content hash.
- The `watch --format sarif` run emits a SARIF 2.1.0 log with one `result`
  (rule `page-changed-significantly`, level `warning`) pointing at the URL,
  carrying the change ratio and added/removed line counts in `properties`.
- `--fail-on-change` exits non-zero, so a scheduler or CI job treats the change
  as an actionable signal.

## How to act

Open the diff
(`archivesnap diff "https://acme.example/security/ACME-SA-2026-014" --store demos/01-vendor-security-advisory/snaps`),
confirm the severity escalated and a fixed version shipped, then route it to the
patch-management owner per your runbook. Leave the new snapshot in place so the
next advisory update diffs against it.
