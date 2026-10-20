import test from 'node:test';
import assert from 'node:assert/strict';
import { createPostgresWorker } from '../src/postgres-worker.mjs';

const claimedEvent = {
  eventKey: 'event-key-1',
  status: 'processing',
  payload: { action: 'opened' },
  lease: { workerId: 'worker-a', token: 'lease-token-1', until: '2026-10-20T04:00:30.000Z' }
};

function fakeQueue(overrides = {}) {
  const calls = { claim: [], extend: [], complete: [], fail: [] };
  return {
    calls,
    async claimNext(args) { calls.claim.push(args); return claimedEvent; },
    async extendLease(args) { calls.extend.push(args); return claimedEvent; },
    async complete(args) { calls.complete.push(args); return { ...claimedEvent, status: 'succeeded' }; },
    async fail(args) { calls.fail.push(args); return { ...claimedEvent, status: args.retryable ? 'retry_wait' : 'dead_letter' }; },
    ...overrides
  };
}

const goodResult = {
  resultEvidence: { verified: true, evidenceRef: 'github:issue:451', method: 'read-after-write' },
  value: { issueNumber: 451 }
};

function wait(ms) { return new Promise(resolve => setTimeout(resolve, ms)); }

async function waitFor(predicate, timeoutMs = 500) {
  const started = Date.now();
  while (!predicate()) {
    if (Date.now() - started > timeoutMs) throw new Error('test_wait_timed_out');
    await wait(2);
  }
}

test('worker renews the lease while execute is running and only completes with verified evidence', async () => {
  const queue = fakeQueue();
  const worker = createPostgresWorker({
    queue, workerId: 'worker-a', leaseMs: 300, heartbeatMs: 5,
    execute: async (_event, context) => {
      await waitFor(() => queue.calls.extend.length >= 2);
      assert.equal(context.workerId, 'worker-a');
      assert.equal(context.leaseToken, claimedEvent.lease.token);
      assert.equal(context.signal.aborted, false);
      return goodResult;
    }
  });

  const result = await worker.runOnce();
  assert.equal(result.status, 'succeeded');
  assert.ok(queue.calls.extend.length >= 2);
  assert.equal(queue.calls.complete.length, 1);
  assert.equal(queue.calls.complete[0].resultEvidence, goodResult.resultEvidence);
  assert.equal(queue.calls.fail.length, 0);
});

test('worker fences execution after a heartbeat failure and does not settle stale lease', async () => {
  const queue = fakeQueue({
    async extendLease(args) {
      queue.calls.extend.push(args);
      throw new Error('event_lease_mismatch_or_expired');
    }
  });
  let receivedSignal;
  const worker = createPostgresWorker({
    queue, workerId: 'worker-a', leaseMs: 300, heartbeatMs: 5,
    execute: (_event, context) => {
      receivedSignal = context.signal;
      return new Promise((_resolve, reject) => {
        context.signal.addEventListener('abort', () => reject(context.signal.reason), { once: true });
      });
    }
  });

  const result = await worker.runOnce();
  assert.equal(result.status, 'lease_lost');
  assert.equal(receivedSignal.aborted, true);
  assert.equal(queue.calls.complete.length, 0);
  assert.equal(queue.calls.fail.length, 0);
});

test('worker sends execution errors through bounded queue failure settlement', async () => {
  const queue = fakeQueue();
  const worker = createPostgresWorker({
    queue, workerId: 'worker-a', leaseMs: 300, heartbeatMs: 10,
    maxAttempts: 3,
    isRetryableError: error => /503/.test(error.message),
    execute: async () => { throw new Error('upstream HTTP 503'); }
  });

  const result = await worker.runOnce();
  assert.equal(result.status, 'retry_wait');
  assert.equal(queue.calls.fail.length, 1);
  assert.equal(queue.calls.fail[0].retryable, true);
  assert.equal(queue.calls.fail[0].maxAttempts, 3);
  assert.equal(queue.calls.complete.length, 0);
});

test('worker refuses to mark success when execute does not return independent verification evidence', async () => {
  const queue = fakeQueue();
  const worker = createPostgresWorker({
    queue, workerId: 'worker-a', leaseMs: 300, heartbeatMs: 10,
    execute: async () => ({ value: 'done but unverified' })
  });

  const result = await worker.runOnce();
  assert.equal(result.status, 'dead_letter');
  assert.equal(queue.calls.complete.length, 0);
  assert.equal(queue.calls.fail.length, 1);
  assert.equal(queue.calls.fail[0].retryable, false);
});

test('worker treats uncertain completion settlement as ambiguous and never follows with fail', async () => {
  const queue = fakeQueue({
    async complete(args) { queue.calls.complete.push(args); throw new Error('connection lost after COMMIT'); }
  });
  const worker = createPostgresWorker({
    queue, workerId: 'worker-a', leaseMs: 300, heartbeatMs: 20,
    execute: async () => goodResult
  });

  const result = await worker.runOnce();
  assert.equal(result.status, 'settlement_error');
  assert.equal(queue.calls.complete.length, 1);
  assert.equal(queue.calls.fail.length, 0);
});

test('worker start and stop interrupts idle polling without claiming extra work', async () => {
  const calls = { claim: 0 };
  const queue = fakeQueue({
    async claimNext() { calls.claim += 1; return null; }
  });
  const worker = createPostgresWorker({
    queue, workerId: 'worker-a', pollIntervalMs: 60_000,
    execute: async () => goodResult
  });
  const loop = worker.start();
  await waitFor(() => calls.claim === 1);
  await worker.stop();
  await loop;
  assert.equal(calls.claim, 1);
  assert.equal(worker.isRunning, false);
});

test('worker validates required queue methods, identity and lease timing', () => {
  assert.throws(() => createPostgresWorker({ workerId: 'worker-a', execute: () => goodResult }), /queue must implement/);
  assert.throws(() => createPostgresWorker({ queue: fakeQueue(), workerId: ' ', execute: () => goodResult }), /workerId is required/);
  assert.throws(() => createPostgresWorker({ queue: fakeQueue(), workerId: 'worker-a', execute: () => goodResult, leaseMs: 100, heartbeatMs: 100 }), /heartbeatMs must be an integer/);
});