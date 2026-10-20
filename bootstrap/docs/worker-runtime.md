# UAW PostgreSQL worker runtime

`npm run start:worker` is a separate long-running process. It deliberately does not include an example business executor or infer permission to mutate provider resources.

## Required host configuration

- `UAW_DATABASE_URL`: PostgreSQL URL for the **runtime role**, not the migration/admin role.
- `UAW_WORKER_ID`: unique safe identifier per process/replica; duplicate IDs make operational diagnosis unreliable.
- `UAW_EXECUTOR_MODULE`: absolute path to a locally managed `.mjs`/`.js` module that exports `executeEvent(event, { signal, workerId, leaseToken })`.

Optional settings:

| Variable | Default | Bounds |
|---|---:|---:|
| `UAW_WORKER_LEASE_MS` | 30000 | 100–3600000 ms |
| `UAW_WORKER_HEARTBEAT_MS` | lease / 3 | 1–lease−1 ms |
| `UAW_WORKER_POLL_INTERVAL_MS` | 1000 | 1–3600000 ms |
| `UAW_WORKER_MAX_ATTEMPTS` | 5 | 1–100 |
| `UAW_WORKER_BASE_DELAY_MS` | 1000 | 0–86400000 ms |
| `UAW_WORKER_MAX_DELAY_MS` | 3600000 | base delay–86400000 ms |

The module may export `isRetryableError(error)` to distinguish transient failures. It must honour `AbortSignal`, bound all external I/O with timeouts, apply the UAW policy/approval engine, and reconcile ambiguous writes before a retry. It may return `{ value, resultEvidence }`, but `resultEvidence` must only state `verified: true` after independent provider read-back or equivalent evidence; the runner rejects missing/empty evidence.

The process fails closed unless the `pg` Node package is installed, the DB is reachable, all three queue tables exist in `public`, and the explicit executor module loads and exports the required function. It logs only structured stage/code identifiers for database/executor startup failures, not exception messages or credentials. SIGTERM/SIGINT stop new claims, allow the current event execution/settlement to finish, and then close the DB pool. The host executor must enforce its own deadlines so graceful shutdown cannot wait forever on a stuck network operation.

## Security and rollout boundaries

- Apply `schemas/postgres-event-inbox.sql` with a migration role before starting the process.
- Use a runtime DB role with only schema USAGE, queue table SELECT/INSERT/UPDATE, and required sequence USAGE/SELECT; do not run with the migration owner in production.
- Store the URL and provider credentials in the platform's secret facility, not Git or logs.
- Deploy ingress and workers separately; do not expose the ingress publicly until TLS, proxy limits, provider subscription configuration, replay policy and network ACLs are reviewed.
- `npm run test:e2e` uses an in-memory queue-contract double. The opt-in `UAW_TEST_DATABASE_URL` suite is still required to establish PostgreSQL transaction/concurrency/permission behaviour on the target version.