-- UAW durable event inbox for PostgreSQL 14+.
-- Execute with the migration role before enabling workers.
-- The application role should receive only the minimum required table privileges.
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