import { createHash, randomUUID } from 'node:crypto';
import { verifyHmacSha256 } from './event-inbox.mjs';

export const POSTGRES_EVENT_QUEUE_SCHEMA = String.raw`
CREATE TABLE IF NOT EXISTS uaw_event_sources (
  provider text PRIMARY KEY,
  paused boolean NOT NULL DEFAULT false,
  reason text,
  updated_at timestamptz NOT NULL DEFAULT clock_timestamp()
);

CREATE TABLE IF NOT EXISTS uaw_event_inbox (
  id bigserial PRIMARY KEY,
  event_key text NOT NULL UNIQUE,
  provider text NOT NULL,
  provider_event_id text NOT NULL,
  body_sha256 char(64) NOT NULL,
  payload jsonb NOT NULL,
  trusted_internal boolean NOT NULL DEFAULT false,
  status text NOT NULL DEFAULT 'queued'
    CHECK (status IN ('queued', 'processing', 'retry_wait', 'succeeded', 'dead_letter')),
  received_at timestamptz NOT NULL DEFAULT clock_timestamp(),
  attempts integer NOT NULL DEFAULT 0 CHECK (attempts >= 0),
  max_attempts integer NOT NULL DEFAULT 5 CHECK (max_attempts >= 1),
  next_attempt_at timestamptz NOT NULL DEFAULT clock_timestamp(),
  lease_owner text,
  lease_token uuid,
  lease_until timestamptz,
  result_evidence jsonb,
  last_error text,
  completed_at timestamptz,
  dead_lettered_at timestamptz,
  redrive_count integer NOT NULL DEFAULT 0 CHECK (redrive_count >= 0),
  UNIQUE (provider, provider_event_id),
  CHECK (
    (status = 'processing' AND lease_owner IS NOT NULL AND lease_token IS NOT NULL AND lease_until IS NOT NULL)
    OR
    (status <> 'processing' AND lease_owner IS NULL AND lease_token IS NULL AND lease_until IS NULL)
  )
);

CREATE INDEX IF NOT EXISTS uaw_event_inbox_due_idx
  ON uaw_event_inbox (next_attempt_at, received_at, id)
  WHERE status IN ('queued', 'retry_wait');
CREATE INDEX IF NOT EXISTS uaw_event_inbox_expired_lease_idx
  ON uaw_event_inbox (lease_until, received_at, id)
  WHERE status = 'processing';
CREATE INDEX IF NOT EXISTS uaw_event_inbox_dead_letter_idx
  ON uaw_event_inbox (dead_lettered_at DESC)
  WHERE status = 'dead_letter';

CREATE TABLE IF NOT EXISTS uaw_event_attempts (
  id bigserial PRIMARY KEY,
  event_key text NOT NULL REFERENCES uaw_event_inbox(event_key) ON DELETE RESTRICT,
  attempt_number integer NOT NULL,
  worker_id text NOT NULL,
  lease_token uuid NOT NULL UNIQUE,
  claimed_at timestamptz NOT NULL,
  lease_until timestamptz NOT NULL,
  finished_at timestamptz,
  outcome text CHECK (outcome IN ('succeeded', 'retry_wait', 'dead_letter', 'lease_expired')),
  error_text text,
  result_evidence jsonb,
  UNIQUE (event_key, attempt_number)
);
`;

function requiredString(value, name) {
  if (typeof value !== 'string' || !value.trim() || /[\u0000-\u001f]/.test(value)) {
    throw new TypeError(`${name} is required and must not contain control characters`);
  }
  return value;
}

function toDate(value, name = 'now') {
  const date = value instanceof Date ? new Date(value.getTime()) : new Date(value);
  if (!Number.isFinite(date.getTime())) throw new TypeError(`${name} must be a valid timestamp`);
  return date;
}

function stableEventKey(provider, providerEventId) {
  // JSON tuple encoding avoids collisions such as ('a', 'b:c') vs ('a:b', 'c').
  return createHash('sha256').update(JSON.stringify([provider, providerEventId])).digest('hex');
}

function safeErrorMessage(error) {
  return String(error?.message ?? error ?? 'unknown_error')
    .replace(/(Bearer\s+)[A-Za-z0-9._~+/-]+=*/gi, '$1[REDACTED]')
    .replace(/((?:access[_-]?token|refresh[_-]?token|api[_-]?key|password|secret|authorization)\s*[:=]\s*)[^\s,;&]+/gi, '$1[REDACTED]')
    .slice(0, 500);
}

function mapRow(row) {
  if (!row) return null;
  return {
    eventKey: row.event_key,
    provider: row.provider,
    eventId: row.provider_event_id,
    bodySha256: String(row.body_sha256).trim(),
    payload: row.payload,
    trustedInternal: row.trusted_internal,
    status: row.status,
    receivedAt: toDate(row.received_at).toISOString(),
    attempts: row.attempts,
    maxAttempts: row.max_attempts,
    nextAttemptAt: toDate(row.next_attempt_at).toISOString(),
    lease: row.lease_token ? {
      workerId: row.lease_owner,
      token: row.lease_token,
      until: toDate(row.lease_until).toISOString()
    } : null,
    resultEvidence: row.result_evidence,
    lastError: row.last_error,
    completedAt: row.completed_at ? toDate(row.completed_at).toISOString() : null,
    deadLetteredAt: row.dead_lettered_at ? toDate(row.dead_lettered_at).toISOString() : null,
    redriveCount: row.redrive_count
  };
}

async function inTransaction(pool, operation) {
  const client = await pool.connect();
  try {
    await client.query('BEGIN');
    const result = await operation(client);
    await client.query('COMMIT');
    return result;
  } catch (error) {
    try { await client.query('ROLLBACK'); } catch { /* retain the original error */ }
    throw error;
  } finally {
    client.release();
  }
}

/**
 * PostgreSQL-backed event queue compatible with a node-postgres Pool.
 * The host must verify/provider-normalize the official signature format and keep secrets
 * outside this module. Webhook ingress here supports HMAC-SHA256 over the exact raw JSON body.
 */
export function createPostgresEventQueue({ pool, uuid = randomUUID } = {}) {
  if (!pool || typeof pool.query !== 'function' || typeof pool.connect !== 'function') {
    throw new TypeError('pool must implement the node-postgres Pool query/connect contract');
  }
  if (typeof uuid !== 'function') throw new TypeError('uuid must be a function');

  async function insertOnce({ provider, eventId, rawBody, payload, trustedInternal, maxAttempts, now }) {
    provider = requiredString(provider, 'provider');
    eventId = requiredString(eventId, 'eventId');
    if (!Number.isInteger(maxAttempts) || maxAttempts < 1 || maxAttempts > 100) {
      throw new TypeError('maxAttempts must be an integer from 1 to 100');
    }
    const timestamp = now === undefined ? null : toDate(now);
    const bodyBytes = rawBody === undefined
      ? Buffer.from(JSON.stringify(payload ?? null), 'utf8')
      : typeof rawBody === 'string' ? Buffer.from(rawBody, 'utf8') : Buffer.from(rawBody);
    const body = bodyBytes.toString('utf8');
    let normalizedPayload = payload;
    if (rawBody !== undefined) {
      try { normalizedPayload = JSON.parse(body); }
      catch { throw new TypeError('rawBody must contain valid JSON'); }
      if (payload !== undefined && JSON.stringify(payload) !== JSON.stringify(normalizedPayload)) {
        throw new TypeError('payload must match the JSON decoded from rawBody');
      }
    }
    const bodySha256 = createHash('sha256').update(bodyBytes).digest('hex');
    const eventKey = stableEventKey(provider, eventId);
    const result = await pool.query(
      `INSERT INTO uaw_event_inbox
        (event_key, provider, provider_event_id, body_sha256, payload, trusted_internal, max_attempts, received_at, next_attempt_at)
       VALUES ($1, $2, $3, $4, $5::jsonb, $6, $7,
               COALESCE($8::timestamptz, clock_timestamp()),
               COALESCE($8::timestamptz, clock_timestamp()))
       ON CONFLICT (provider, provider_event_id) DO NOTHING
       RETURNING *`,
      [eventKey, provider, eventId, bodySha256, JSON.stringify(normalizedPayload ?? null), trustedInternal, maxAttempts, timestamp]
    );
    if (result.rows?.[0]) return { duplicate: false, event: mapRow(result.rows[0]) };

    const existing = await pool.query(
      'SELECT * FROM uaw_event_inbox WHERE provider = $1 AND provider_event_id = $2',
      [provider, eventId]
    );
    const row = existing.rows?.[0];
    if (!row) throw new Error('event_conflict_row_not_visible');
    if (String(row.body_sha256).trim() !== bodySha256) {
      const error = new Error('event_id_payload_mismatch');
      error.code = 'event_id_payload_mismatch';
      throw error;
    }
    return { duplicate: true, event: mapRow(row) };
  }

  return Object.freeze({
    async initialize() {
      await pool.query(POSTGRES_EVENT_QUEUE_SCHEMA);
      return { initialized: true, schema: 'uaw-event-queue-v1' };
    },

    async ingestWebhook({ provider, eventId, rawBody, signature, secret, signaturePrefix = 'sha256=', maxAttempts = 5, now } = {}) {
      if (typeof rawBody !== 'string' && !(rawBody instanceof Uint8Array)) {
        throw new TypeError('rawBody must be the exact raw request body');
      }
      if (!verifyHmacSha256({ rawBody, signature, secret, prefix: signaturePrefix })) {
        const error = new Error('webhook_signature_invalid');
        error.code = 'webhook_signature_invalid';
        throw error;
      }
      return insertOnce({ provider, eventId, rawBody, trustedInternal: false, maxAttempts, now });
    },

    async enqueueInternal({ eventId, payload, maxAttempts = 5, now } = {}) {
      if (payload === undefined) throw new TypeError('payload is required');
      return insertOnce({ provider: 'uaw-internal', eventId, payload, trustedInternal: true, maxAttempts, now });
    },

    async pauseSource({ provider, reason = 'paused', now = new Date() } = {}) {
      provider = requiredString(provider, 'provider');
      const timestamp = toDate(now);
      await pool.query(
        `INSERT INTO uaw_event_sources (provider, paused, reason, updated_at)
         VALUES ($1, true, $2, $3)
         ON CONFLICT (provider) DO UPDATE SET paused = true, reason = EXCLUDED.reason, updated_at = EXCLUDED.updated_at`,
        [provider, String(reason).slice(0, 200), timestamp]
      );
      return { provider, paused: true };
    },

    async resumeSource({ provider, now = new Date() } = {}) {
      provider = requiredString(provider, 'provider');
      await pool.query(
        `INSERT INTO uaw_event_sources (provider, paused, reason, updated_at)
         VALUES ($1, false, NULL, $2)
         ON CONFLICT (provider) DO UPDATE SET paused = false, reason = NULL, updated_at = EXCLUDED.updated_at`,
        [provider, toDate(now)]
      );
      return { provider, paused: false };
    },

    async claimNext({ workerId, leaseMs = 30_000, now } = {}) {
      workerId = requiredString(workerId, 'workerId');
      if (!Number.isInteger(leaseMs) || leaseMs < 100 || leaseMs > 3_600_000) {
        throw new TypeError('leaseMs must be an integer between 100 and 3600000');
      }
      const timestamp = now === undefined ? null : toDate(now);
      const leaseUntil = timestamp ? new Date(timestamp.getTime() + leaseMs) : null;
      const leaseToken = uuid();
      return inTransaction(pool, async client => {
        // Close expired attempt-history records before the inbox lease is overwritten or cleared.
        await client.query(
          `UPDATE uaw_event_attempts a
           SET finished_at = COALESCE($1::timestamptz, clock_timestamp()), outcome = 'lease_expired',
               error_text = COALESCE(a.error_text, 'worker lease expired')
           FROM uaw_event_inbox e
           WHERE a.event_key = e.event_key AND a.lease_token = e.lease_token
             AND a.finished_at IS NULL AND e.status = 'processing'
             AND e.lease_until <= COALESCE($1::timestamptz, clock_timestamp())`,
          [timestamp]
        );
        await client.query(
          `UPDATE uaw_event_inbox
           SET status = 'dead_letter', lease_owner = NULL, lease_token = NULL, lease_until = NULL,
               dead_lettered_at = COALESCE($1::timestamptz, clock_timestamp()),
               last_error = COALESCE(last_error, 'retry_limit_exceeded_after_interrupted_attempt')
           WHERE attempts >= max_attempts AND (
             (status IN ('queued', 'retry_wait') AND next_attempt_at <= COALESCE($1::timestamptz, clock_timestamp()))
             OR (status = 'processing' AND lease_until <= COALESCE($1::timestamptz, clock_timestamp()))
           )`, [timestamp]
        );
        const candidate = await client.query(
          `SELECT e.* FROM uaw_event_inbox e
           LEFT JOIN uaw_event_sources s ON s.provider = e.provider
           WHERE COALESCE(s.paused, false) = false
             AND e.attempts < e.max_attempts
             AND ((e.status IN ('queued', 'retry_wait') AND e.next_attempt_at <= COALESCE($1::timestamptz, clock_timestamp()))
               OR (e.status = 'processing' AND e.lease_until <= COALESCE($1::timestamptz, clock_timestamp())))
           ORDER BY e.received_at ASC, e.id ASC
           LIMIT 1
           FOR UPDATE OF e SKIP LOCKED`, [timestamp]
        );
        const row = candidate.rows?.[0];
        if (!row) return null;
        const claimed = await client.query(
          `UPDATE uaw_event_inbox
           SET status = 'processing', attempts = attempts + 1,
               lease_owner = $2, lease_token = $3::uuid,
               lease_until = COALESCE($4::timestamptz, clock_timestamp() + ($5::double precision * interval '1 millisecond'))
           WHERE event_key = $1
           RETURNING *`, [row.event_key, workerId, leaseToken, leaseUntil, leaseMs]
        );
        await client.query(
          `INSERT INTO uaw_event_attempts (event_key, attempt_number, worker_id, lease_token, claimed_at, lease_until)
           VALUES ($1, $2, $3, $4::uuid, COALESCE($5::timestamptz, clock_timestamp()), $6)`,
          [row.event_key, row.attempts + 1, workerId, leaseToken, timestamp, claimed.rows?.[0]?.lease_until]
        );
        return mapRow(claimed.rows?.[0]);
      });
    },

    async extendLease({ eventKey, workerId, leaseToken, leaseMs = 30_000, now } = {}) {
      if (!Number.isInteger(leaseMs) || leaseMs < 100 || leaseMs > 3_600_000) {
        throw new TypeError('leaseMs must be an integer between 100 and 3600000');
      }
      const timestamp = now === undefined ? null : toDate(now);
      return inTransaction(pool, async client => {
        const updated = await client.query(
          `WITH lease_time AS (SELECT COALESCE($4::timestamptz, clock_timestamp()) AS at)
           UPDATE uaw_event_inbox e
           SET lease_until = GREATEST(
             e.lease_until,
             lease_time.at + ($5::double precision * interval '1 millisecond')
           )
           FROM lease_time
           WHERE e.event_key = $1 AND e.status = 'processing' AND e.lease_owner = $2
             AND e.lease_token = $3::uuid AND e.lease_until > lease_time.at
           RETURNING e.*`,
          [requiredString(eventKey, 'eventKey'), requiredString(workerId, 'workerId'),
            requiredString(leaseToken, 'leaseToken'), timestamp, leaseMs]
        );
        const row = updated.rows?.[0];
        if (!row) throw new Error('event_lease_mismatch_or_expired');
        const attempt = await client.query(
          `UPDATE uaw_event_attempts a SET lease_until = $2
           FROM uaw_event_inbox e
           WHERE a.lease_token = $1::uuid AND a.finished_at IS NULL
             AND a.event_key = e.event_key AND e.lease_token = a.lease_token
             AND e.lease_until = $2`,
          [leaseToken, row.lease_until]
        );
        if (attempt.rowCount !== 1) throw new Error('event_attempt_audit_missing');
        return mapRow(row);
      });
    },

    async complete({ eventKey, workerId, leaseToken, resultEvidence, now } = {}) {
      if (!resultEvidence || resultEvidence.verified !== true || typeof resultEvidence.evidenceRef !== 'string' || !resultEvidence.evidenceRef.trim()) {
        throw new TypeError('verified resultEvidence with a non-empty evidenceRef is required');
      }
      const timestamp = now === undefined ? null : toDate(now);
      return inTransaction(pool, async client => {
        const updated = await client.query(
          `WITH completion_time AS (
             SELECT COALESCE($5::timestamptz, clock_timestamp()) AS at
           )
           UPDATE uaw_event_inbox e
           SET status = 'succeeded',
               result_evidence = jsonb_set($4::jsonb, '{verifiedAt}', to_jsonb(completion_time.at), true),
               completed_at = completion_time.at,
               lease_owner = NULL, lease_token = NULL, lease_until = NULL, last_error = NULL
           FROM completion_time
           WHERE e.event_key = $1 AND e.status = 'processing' AND e.lease_owner = $2
             AND e.lease_token = $3::uuid AND e.lease_until > completion_time.at
           RETURNING e.*`,
          [requiredString(eventKey, 'eventKey'), requiredString(workerId, 'workerId'),
            requiredString(leaseToken, 'leaseToken'), JSON.stringify({
              verified: true, evidenceRef: resultEvidence.evidenceRef,
              method: resultEvidence.method ?? null
            }), timestamp]
        );
        const row = updated.rows?.[0];
        if (!row) throw new Error('event_lease_mismatch_or_expired');
        await client.query(
          `UPDATE uaw_event_attempts SET finished_at = $2, outcome = 'succeeded', result_evidence = $3::jsonb
           WHERE lease_token = $1::uuid AND finished_at IS NULL`,
          [leaseToken, row.completed_at, JSON.stringify(resultEvidence)]
        );
        return mapRow(row);
      });
    },

    async fail({ eventKey, workerId, leaseToken, error, retryable = true, maxAttempts = 5,
      baseDelayMs = 1_000, maxDelayMs = 3_600_000, now } = {}) {
      if (!Number.isInteger(maxAttempts) || maxAttempts < 1 || maxAttempts > 100) throw new TypeError('maxAttempts must be an integer from 1 to 100');
      if (!Number.isFinite(baseDelayMs) || baseDelayMs < 0 || !Number.isFinite(maxDelayMs) || maxDelayMs < baseDelayMs) throw new TypeError('invalid retry delay bounds');
      const suppliedTimestamp = now === undefined ? null : toDate(now);
      return inTransaction(pool, async client => {
        const currentResult = await client.query(
          `SELECT *, COALESCE($4::timestamptz, clock_timestamp()) AS database_now
           FROM uaw_event_inbox
           WHERE event_key = $1 AND status = 'processing' AND lease_owner = $2
             AND lease_token = $3::uuid AND lease_until > COALESCE($4::timestamptz, clock_timestamp())
           FOR UPDATE`,
          [requiredString(eventKey, 'eventKey'), requiredString(workerId, 'workerId'), requiredString(leaseToken, 'leaseToken'), suppliedTimestamp]
        );
        const current = currentResult.rows?.[0];
        if (!current) throw new Error('event_lease_mismatch_or_expired');
        const timestamp = suppliedTimestamp ?? toDate(current.database_now);
        const canRetry = retryable && current.attempts < Math.min(maxAttempts, current.max_attempts);
        const delay = canRetry ? Math.min(maxDelayMs, baseDelayMs * (2 ** Math.max(0, current.attempts - 1))) : null;
        const nextAttemptAt = delay === null ? timestamp : new Date(timestamp.getTime() + delay);
        const status = canRetry ? 'retry_wait' : 'dead_letter';
        const safeError = safeErrorMessage(error);
        const updated = await client.query(
          `WITH failure_time AS (SELECT COALESCE($8::timestamptz, clock_timestamp()) AS at)
           UPDATE uaw_event_inbox e
           SET status = $2, max_attempts = LEAST(e.max_attempts, $3), next_attempt_at = $4,
               last_error = $5, dead_lettered_at = CASE WHEN $2 = 'dead_letter' THEN failure_time.at ELSE NULL END,
               lease_owner = NULL, lease_token = NULL, lease_until = NULL
           FROM failure_time
           WHERE e.event_key = $1 AND e.status = 'processing' AND e.lease_owner = $6
             AND e.lease_token = $7::uuid AND e.lease_until > failure_time.at
           RETURNING e.*`,
          [eventKey, status, maxAttempts, nextAttemptAt, safeError, workerId, leaseToken, suppliedTimestamp]
        );
        if (!updated.rows?.[0]) throw new Error('event_lease_mismatch_or_expired');
        await client.query(
          `UPDATE uaw_event_attempts SET finished_at = $2, outcome = $3, error_text = $4
           WHERE lease_token = $1::uuid AND finished_at IS NULL`,
          [leaseToken, updated.rows[0].dead_lettered_at ?? timestamp, status, safeError]
        );
        return { ...mapRow(updated.rows?.[0]), retryAfterMs: delay };
      });
    },

    async redrive({ eventKey, now } = {}) {
      const timestamp = now === undefined ? null : toDate(now);
      const result = await pool.query(
        `UPDATE uaw_event_inbox
         SET status = 'queued', max_attempts = GREATEST(max_attempts, attempts + 5),
             next_attempt_at = COALESCE($2::timestamptz, clock_timestamp()), dead_lettered_at = NULL, lease_owner = NULL, lease_token = NULL,
             lease_until = NULL, completed_at = NULL, last_error = NULL,
             result_evidence = NULL, redrive_count = redrive_count + 1
         WHERE event_key = $1 AND status = 'dead_letter'
         RETURNING *`, [requiredString(eventKey, 'eventKey'), timestamp]
      );
      if (!result.rows?.[0]) throw new Error('event_not_dead_letter');
      return mapRow(result.rows[0]);
    },

    async getEvent({ eventKey } = {}) {
      const result = await pool.query('SELECT * FROM uaw_event_inbox WHERE event_key = $1', [requiredString(eventKey, 'eventKey')]);
      return mapRow(result.rows?.[0]);
    },

    async listDeadLetters({ limit = 100 } = {}) {
      if (!Number.isInteger(limit) || limit < 1 || limit > 1000) throw new TypeError('limit must be between 1 and 1000');
      const result = await pool.query(
        `SELECT * FROM uaw_event_inbox WHERE status = 'dead_letter'
         ORDER BY dead_lettered_at DESC NULLS LAST, id DESC LIMIT $1`, [limit]
      );
      return (result.rows ?? []).map(mapRow);
    }
  });
}