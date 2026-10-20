import test from 'node:test';
import assert from 'node:assert/strict';
import { createHash, createHmac, randomUUID, timingSafeEqual } from 'node:crypto';
import { createWebhookServer } from '../src/webhook-server.mjs';
import { createGitHubWebhookRoute } from '../src/webhooks/provider-routes.mjs';
import { createPostgresWorker } from '../src/postgres-worker.mjs';

const SECRET = 'uaw-e2e-contract-secret';

/**
 * In-memory contract double for the queue interface. This validates the real HTTP -> provider
 * verifier -> queue contract -> worker path, but intentionally does NOT stand in for PostgreSQL's
 * SKIP LOCKED, transaction isolation, or grants; those are covered by the opt-in PG suite.
 */
function createQueueDouble() {
  const events = new Map();
  let executeIngestCount = 0;
  let duplicateCount = 0;

  return {
    events,
    get executeIngestCount() { return executeIngestCount; },
    get duplicateCount() { return duplicateCount; },

    async ingestWebhook({ provider, eventId, rawBody, signature, secret, signaturePrefix = 'sha256=', signedPayload }) {
      const raw = Buffer.isBuffer(rawBody) ? rawBody : Buffer.from(rawBody);
      const signed = signedPayload === undefined ? raw : Buffer.from(signedPayload);
      const expected = `${signaturePrefix}${createHmac('sha256', secret).update(signed).digest('hex')}`;
      const supplied = Buffer.from(String(signature ?? ''), 'utf8');
      const wanted = Buffer.from(expected, 'utf8');
      if (secret !== SECRET || supplied.length !== wanted.length || !timingSafeEqual(supplied, wanted)) {
        const error = new Error('webhook_signature_invalid');
        error.code = 'webhook_signature_invalid';
        throw error;
      }

      const key = `${provider}:${eventId}`;
      const bodyHash = createHash('sha256').update(raw).digest('hex');
      const existing = events.get(key);
      if (existing) {
        if (existing.bodyHash !== bodyHash) {
          const error = new Error('event_id_payload_mismatch');
          error.code = 'event_id_payload_mismatch';
          throw error;
        }
        duplicateCount += 1;
        return { duplicate: true, event: existing };
      }

      const event = {
        eventKey: key,
        provider,
        providerEventId: eventId,
        bodyHash,
        rawBody: Buffer.from(raw),
        payload: JSON.parse(raw.toString('utf8')),
        status: 'queued',
        attempts: 0,
        lease: null,
        resultEvidence: null
      };
      events.set(key, event);
      executeIngestCount += 1;
      return { duplicate: false, event };
    },

    async claimNext({ workerId, leaseMs = 30_000 } = {}) {
      const event = [...events.values()].find(candidate => candidate.status === 'queued');
      if (!event) return null;
      event.status = 'processing';
      event.attempts += 1;
      event.lease = { token: randomUUID(), workerId, until: Date.now() + leaseMs };
      return { ...event, lease: { ...event.lease } };
    },

    async extendLease({ eventKey, workerId, leaseToken, leaseMs = 30_000 } = {}) {
      const event = [...events.values()].find(candidate => candidate.eventKey === eventKey);
      if (!event || event.status !== 'processing' || event.lease?.workerId !== workerId ||
          event.lease?.token !== leaseToken || event.lease.until <= Date.now()) {
        throw new Error('event_lease_mismatch_or_expired');
      }
      event.lease.until = Math.max(event.lease.until, Date.now() + leaseMs);
      return event;
    },

    async complete({ eventKey, workerId, leaseToken, resultEvidence } = {}) {
      const event = [...events.values()].find(candidate => candidate.eventKey === eventKey);
      if (!event || event.status !== 'processing' || event.lease?.workerId !== workerId ||
          event.lease?.token !== leaseToken || event.lease.until <= Date.now()) {
        throw new Error('event_lease_mismatch_or_expired');
      }
      if (resultEvidence?.verified !== true || typeof resultEvidence.evidenceRef !== 'string' || !resultEvidence.evidenceRef) {
        throw new TypeError('verified resultEvidence is required');
      }
      event.status = 'succeeded';
      event.resultEvidence = structuredClone(resultEvidence);
      event.completedAt = new Date().toISOString();
      event.lease = null;
      return event;
    },

    async fail({ eventKey, workerId, leaseToken, error, retryable } = {}) {
      const event = [...events.values()].find(candidate => candidate.eventKey === eventKey);
      if (!event || event.status !== 'processing' || event.lease?.workerId !== workerId ||
          event.lease?.token !== leaseToken) throw new Error('event_lease_mismatch_or_expired');
      event.status = retryable ? 'retry_wait' : 'dead_letter';
      event.lastError = String(error?.message ?? error);
      event.lease = null;
      return event;
    }
  };
}

test('E2E contract: signed GitHub webhook is enqueued once and the worker independently verifies then completes it', async t => {
  const queue = createQueueDouble();
  const route = createGitHubWebhookRoute({ secret: SECRET });
  const server = createWebhookServer({ queue, routes: [route] });
  await new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(0, '127.0.0.1', resolve);
  });
  t.after(() => new Promise(resolve => server.close(() => resolve())));

  const address = server.address();
  const endpoint = `http://127.0.0.1:${address.port}/webhooks/github`;
  const rawBody = Buffer.from(JSON.stringify({ action: 'opened', number: 451, repository: { full_name: 'dominicusin/example' } }));
  const deliveryId = 'e2e-github-delivery-001';
  const signature = `sha256=${createHmac('sha256', SECRET).update(rawBody).digest('hex')}`;
  const requestOptions = {
    method: 'POST',
    headers: {
      'content-type': 'application/json',
      'x-github-delivery': deliveryId,
      'x-github-event': 'pull_request',
      'x-hub-signature-256': signature
    },
    body: rawBody
  };

  const accepted = await fetch(endpoint, requestOptions);
  assert.equal(accepted.status, 202);
  const acceptedBody = await accepted.json();
  assert.equal(acceptedBody.accepted, true);
  assert.equal(acceptedBody.duplicate, false);
  assert.equal(acceptedBody.eventKey, `github:${deliveryId}`);
  assert.equal(queue.executeIngestCount, 1);

  const duplicate = await fetch(endpoint, requestOptions);
  assert.equal(duplicate.status, 200);
  assert.deepEqual(await duplicate.json(), {
    accepted: true, duplicate: true, eventKey: `github:${deliveryId}`
  });
  assert.equal(queue.executeIngestCount, 1, 'a provider retry must not create another queue event');
  assert.equal(queue.duplicateCount, 1);

  let executorCalls = 0;
  const worker = createPostgresWorker({
    queue,
    workerId: 'e2e-worker-1',
    leaseMs: 5_000,
    heartbeatMs: 1_000,
    pollIntervalMs: 5,
    execute: async (event, { signal, workerId, leaseToken }) => {
      executorCalls += 1;
      assert.equal(signal.aborted, false);
      assert.equal(workerId, 'e2e-worker-1');
      assert.ok(leaseToken);
      assert.equal(event.provider, 'github');
      assert.equal(event.providerEventId, deliveryId);
      assert.deepEqual(event.payload, JSON.parse(rawBody.toString('utf8')));
      return {
        value: { action: 'readback-verified', pullRequest: 451 },
        resultEvidence: {
          verified: true,
          evidenceRef: 'e2e:github:pull-request:451:read-after-write',
          method: 'independent-read-after-write'
        }
      };
    }
  });

  const processed = await worker.runOnce();
  assert.equal(processed.status, 'succeeded');
  assert.equal(processed.eventKey, `github:${deliveryId}`);
  assert.equal(processed.value.pullRequest, 451);
  assert.equal(executorCalls, 1, 'the event must execute once despite a duplicate delivery');

  const stored = queue.events.get(`github:${deliveryId}`);
  assert.equal(stored.status, 'succeeded');
  assert.equal(stored.attempts, 1);
  assert.equal(stored.resultEvidence.verified, true);
  assert.equal(stored.resultEvidence.method, 'independent-read-after-write');
  assert.equal(stored.lease, null);
});