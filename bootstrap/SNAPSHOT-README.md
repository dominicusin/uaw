# UAW bootstrap source snapshot

This directory preserves the reviewable source snapshot for UAW event-ingress and durable-worker work completed on 2026-10-20.

## Included

- PostgreSQL queue and worker implementations, DDL, and worker lease tests.
- HTTP webhook ingress, runtime configuration, and GitHub/Linear/Calendly signature profiles.
- Worker/ingress entrypoints and documentation.
- Integration registry, local test/validation logs, and the UAW audit report under `docs/audit/`.

## Verification evidence

The complete local package's captured checks reported:
- `npm run check`: 109 passed, 0 failed, 1 skipped.
- Registry: 18 integrations — 9 connected, 5 partial, 4 unavailable.
- The skipped test is the opt-in live PostgreSQL integration suite; no successful live PostgreSQL run is claimed.
- Contract E2E passed against an in-memory queue double; this is not DB-backed production E2E.

The repository-root workflow `.github/workflows/uaw-bootstrap-check.yml` checks JavaScript syntax and JSON evidence for this source snapshot. It does **not** resolve all imports, run the complete original npm suite, or validate a live PostgreSQL database.

## Snapshot boundary

This is a reviewable supplemental source snapshot within the existing Python UAW repository, not a claim that every file from the generated bootstrap ZIP has been mirrored here or that `bootstrap/` is a standalone runnable package. The canonical package manifest, every adapter, the full test tree, and the original package's checksum manifest are not all replicated here yet. The preserved `bootstrap/.github/workflows/ci.yml` is a reference file; GitHub Actions does not discover workflows nested below the repository root workflow directory.

## Not production-ready

- No live database, public webhook endpoint, or long-running worker was deployed.
- Provider secrets/subscriptions have not been installed.
- A policy-checked host executor must be explicitly configured.
- Workflow `demo-001` remains Blocked until real DB-backed verification and provider access are available.

Do not infer production readiness from local unit/contract tests alone.
