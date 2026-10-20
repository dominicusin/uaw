# PostgreSQL event queue adapter

`src/postgres-event-queue.mjs` implements a durable multi-process event inbox against the `node-postgres` Pool contract. It is a provider-neutral queue core, not an HTTP server and not a finished provider webhook receiver.

## Guarantees implemented by the adapter

- Database uniqueness on `(provider, provider_event_id)` and a stable, payload-independent event key.
- HMAC-SHA256 validation against the exact raw request bytes before a webhook write is issued. The receiver must pass the untouched body bytes and a signature already extracted into the `sha256=<hex>` form.
- Atomic claim transactions using `FOR UPDATE SKIP LOCKED`, per-attempt lease tokens (fencing token), and an attempt-history table.
- Stale lease reclamation; attempts are recorded as `lease_expired` before the lease is replaced.
- `extendLease()` heartbeat for long-running work. It only renews a still-live owner/token lease, never shortens the current deadline, and updates the attempt-history deadline in the same transaction.
- Completion requires a verified evidence reference and a still-valid owner/token lease. Failures use bounded exponential backoff with redacted error text.
- Provider pause/resume, dead-letter listing and explicit dead-letter redrive. Redrive preserves lifetime attempt history rather than reusing old attempt numbers.

The queue stores the decoded JSON event body but deliberately does not store the webhook signature or signing secret. Provider-specific signature header decoding must be done at the HTTP boundary; providers whose signature format is not plain `sha256=<hex>` need a provider-specific verifier before enabling ingress.

## Schema setup

Apply `schemas/postgres-event-inbox.sql` with a database migration role before starting workers. Alternatively, `queue.initialize()` runs the same `CREATE TABLE/INDEX IF NOT EXISTS` batch and should only be called by a role permitted to create schema objects. For normal runtime operations, provision a least-privilege database role separately; avoid granting schema ownership to the application process.

PostgreSQL's shared row locks and unique constraints are the cross-process coordination mechanism. The JSON file inbox remains useful for local demos but is **not** a distributed queue.

## Minimal wiring example

```js
import pg from 'pg';
import { createPostgresEventQueue } from './src/postgres-event-queue.mjs';

const pool = new pg.Pool({ connectionString: process.env.UAW_DATABASE_URL });
const queue = createPostgresEventQueue({ pool });

// Run migrations separately in production. `initialize()` is shown only for a
// disposable development database whose database role is allowed to create tables.
// await queue.initialize();

// The HTTP framework must preserve request bytes before JSON parsing.
// The provider's header has to be decoded into `sha256=<hex>` before this call.
const accepted = await queue.ingestWebhook({
  provider: 'github',
  eventId: request.headers['x-github-delivery'],
  rawBody: request.rawBody,
  signature: `sha256=${request.headers['x-uaw-signature']}`,
  secret: secretStore.get('github-webhook-secret')
});

if (accepted.duplicate) return { status: 202, duplicate: true };
return { status: 202, eventKey: accepted.event.eventKey };
```

The sample assumes the HTTP layer has validated the provider event ID and transformed the provider's documented signature format into the queue's `sha256=<hex>` contract. Do not copy that transformation for a different provider without checking its official signing scheme.

## Worker lifecycle

1. `claimNext({ workerId, leaseMs })` obtains a transactionally claimed event and a new lease token.
2. Execute a bounded, policy-checked UAW workflow. For work that may outlast its lease, periodically call `extendLease({ eventKey, workerId, leaseToken, leaseMs })` before expiration. Renewal requires the same live lease and extends from the database's current time without shortening a longer existing deadline.
3. If renewal fails, stop starting further work and treat the result of any already-issued external mutation as uncertain; reconcile it before attempting a replay. Queue fencing prevents stale completion/settlement but does not cancel an external API request already in flight.
4. On independently verified success, call `complete({ eventKey, workerId, leaseToken, resultEvidence })`.
5. On known failure, call `fail({ ..., retryable, maxAttempts })`. A stale or expired lease is rejected. Inspect exhausted events with `listDeadLetters()` and redrive only after an operator/policy decision.
6. `pauseSource`/`resumeSource` stop or restore dispatch for a provider; ingress may continue persisting new messages while dispatch is paused.

## Validation limits

The local unit/contract suite uses a mock `Pool` and validates SQL call sequencing, rollback paths, lease fencing/renewal, deduplication and retry policies. The current run reports **67 passed, 0 failed and one skipped**. The skipped test is an opt-in real-database suite enabled with `UAW_TEST_DATABASE_URL` and the optional `pg` package; it creates a temporary schema, exercises concurrent claims/retry/redrive, then removes that schema.

For a meaningful least-privilege test, set `UAW_TEST_DATABASE_URL` to a disposable migration/admin role that can create/drop a temporary schema and grant privileges, and `UAW_TEST_RUNTIME_DATABASE_URL` to a separate login in the **same database**. The harness creates the schema as the migration role, applies the DDL, and grants the runtime role schema `USAGE`, table `SELECT/INSERT/UPDATE`, and sequence `USAGE/SELECT`. When the roles differ, the test asserts that the runtime role cannot create schema objects, delete events or truncate the inbox. If `UAW_TEST_RUNTIME_DATABASE_URL` is omitted, the suite uses the admin URL for both and does **not** verify separation of runtime privileges.

This environment has no `psql`/PostgreSQL server and did not execute that integration suite. Treat the target PostgreSQL version, privileges, connection pooling and concurrency behavior as deployment gates until the opt-in suite passes in the target environment.

## Reference worker runner

`src/postgres-worker.mjs` adds a cooperative sequential runner around the queue contract. It is deliberately not a policy engine and does not make provider calls itself. The injected `execute` function must run the normal UAW policy executor and return evidence produced by an independent read-after-write/health check; the runner refuses a success result that lacks `resultEvidence.verified === true` and a non-empty `resultEvidence.evidenceRef`.

```js
import pg from 'pg';
import { createPostgresEventQueue } from './src/postgres-event-queue.mjs';
import { createPostgresWorker } from './src/postgres-worker.mjs';

const pool = new pg.Pool({ connectionString: process.env.UAW_DATABASE_URL });
const queue = createPostgresEventQueue({ pool });
const worker = createPostgresWorker({
  queue,
  workerId: process.env.UAW_WORKER_ID,
  leaseMs: 30_000,
  heartbeatMs: 10_000,
  execute: async (event, { signal }) => {
    // Replace with your policy-checked executor; it must support AbortSignal and reconciliation.
    const verified = await runAllowedWorkflowAndVerify(event, { signal });
    return { resultEvidence: verified.evidence, value: verified.output };
  },
  onError: ({ error, stage, eventKey }) => console.error({ stage, eventKey, message: error.message })
});

process.once('SIGTERM', () => { void worker.stop(); });
process.once('SIGINT', () => { void worker.stop(); });
try {
  await worker.start();
} finally {
  await pool.end();
}
```

Operational behavior:

- One worker processes one event at a time; horizontal scale comes from multiple processes sharing the PostgreSQL queue.
- The runner refreshes leases serially and aborts the injected operation if renewal fails. Work that ignores the signal may still have an external request in flight; lease fencing cannot undo that request.
- An execution exception is passed to `queue.fail()` with bounded retry settings. Configure `isRetryableError` so permanent policy/validation failures do not retry.
- Missing independent evidence is a non-retryable failure. A connection error during `complete()` or `fail()` is returned as `settlement_error`; the runner does not attempt a second settlement because the first transaction may already have committed.
- Graceful `stop()` stops polling and wakes an idle worker, but lets the current event finish while heartbeats continue. Ensure service-manager termination grace periods exceed the longest allowed workflow or implement a separate bounded shutdown protocol.
- The sample intentionally omits provider credentials, HTTP ingress, workflow routing and any production action implementation. Do not use the illustrative `runAllowedWorkflowAndVerify` identifier as if it were a function included in this package.

The worker runner is covered by mock-contract tests for successful heartbeat, lease loss/abort, retry classification, missing evidence, ambiguous completion and graceful stop. These tests do not replace the opt-in live PostgreSQL suite.