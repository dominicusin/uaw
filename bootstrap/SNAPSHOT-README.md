# UAW bootstrap source snapshot

This directory contains the reviewed source snapshot for the UAW event-ingress and durable-worker work completed on 2026-10-20.

## Contents

- PostgreSQL event inbox/queue implementation and DDL.
- Worker runner implementation and heartbeat/lease contract tests.
- HTTP webhook ingress, GitHub/Linear/Calendly signature profiles and startup scripts.
- Provider route configuration and runtime documentation.
- Test logs and integration registry captured from the validated local bootstrap package.
- A separate inventory/audit report under `docs/audit/`.

## Verification evidence

The complete local package reported by the maintainer-run check:
- `npm run check`: 109 passed, 0 failed, 1 skipped.
- Registry: 18 integrations; 9 connected, 5 partial, 4 unavailable.
- The skipped test is the opt-in live PostgreSQL integration suite; no successful live PostgreSQL run is claimed.
- The local contract E2E test passed, but it uses an in-memory queue double and is not a DB-backed production E2E test.

## Snapshot boundary

This commit is a reviewable source snapshot inside the existing Python UAW repository, not a claim that every file from the original generated ZIP has been mirrored here or that the snapshot can be run as a standalone package. The canonical package manifest, adapters, full test source tree, and source checksum manifest are not all replicated in this directory yet. The nested workflow document is preserved for review; because it lives under `bootstrap/`, GitHub Actions will not discover it as a repository-root workflow.

## Not production-ready

- No live database, public webhook endpoint, or long-running worker was deployed.
- Provider secrets/subscriptions have not been installed.
- A policy-checked host executor must be explicitly configured.
- The workflow `demo-001` remains Blocked until real DB-backed verification and provider access are available.

Do not infer production readiness from local unit/contract tests alone.
