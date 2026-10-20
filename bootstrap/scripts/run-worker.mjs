import { pathToFileURL } from 'node:url';
import { createPostgresEventQueue } from '../src/postgres-event-queue.mjs';
import { createPostgresWorker } from '../src/postgres-worker.mjs';
import { buildWorkerRuntimeConfig } from '../src/worker-runtime-config.mjs';

let pool;
let worker;
let workerRun;
let shutdownPromise;
let startupStage = 'configuration';

function queueError(code) {
  const error = new Error(code);
  error.code = code;
  return error;
}

async function assertQueueSchema(dbPool) {
  const result = await dbPool.query({
    text: `SELECT to_regclass('public.uaw_event_inbox') AS inbox,
                  to_regclass('public.uaw_event_attempts') AS attempts,
                  to_regclass('public.uaw_event_sources') AS sources`,
    query_timeout: 3_000
  });
  const row = result.rows?.[0];
  if (!row?.inbox || !row?.attempts || !row?.sources) throw queueError('queue_schema_missing');
}

function safeCode(error, fallback) {
  const code = error?.code;
  return typeof code === 'string' && /^[A-Za-z0-9_.-]{1,80}$/.test(code) ? code : fallback;
}

function log(event, fields = {}) {
  process.stdout.write(`${JSON.stringify({ event, ...fields })}\n`);
}

async function main() {
  const config = buildWorkerRuntimeConfig();
  startupStage = 'postgres_package';
  let pg;
  try { pg = await import('pg'); }
  catch { throw queueError('optional_dependency_pg_missing'); }
  const Pool = pg.Pool ?? pg.default?.Pool;
  if (typeof Pool !== 'function') throw queueError('optional_dependency_pg_invalid');

  startupStage = 'database_connect';
  pool = new Pool({
    connectionString: config.databaseUrl,
    max: 2,
    connectionTimeoutMillis: 5_000,
    idleTimeoutMillis: 30_000,
    application_name: 'uaw-event-worker'
  });
  await pool.query({ text: 'SELECT 1', query_timeout: 3_000 });
  startupStage = 'queue_schema';
  await assertQueueSchema(pool);

  startupStage = 'executor_module';
  let executorModule;
  try { executorModule = await import(pathToFileURL(config.executorModule).href); }
  catch { throw queueError('executor_module_load_failed'); }
  if (typeof executorModule.executeEvent !== 'function') throw queueError('executor_module_missing_executeEvent');
  if (executorModule.isRetryableError !== undefined && typeof executorModule.isRetryableError !== 'function') {
    throw queueError('executor_module_invalid_isRetryableError');
  }

  const queue = createPostgresEventQueue({ pool });
  worker = createPostgresWorker({
    queue,
    workerId: config.workerId,
    leaseMs: config.leaseMs,
    heartbeatMs: config.heartbeatMs,
    pollIntervalMs: config.pollIntervalMs,
    maxAttempts: config.maxAttempts,
    baseDelayMs: config.baseDelayMs,
    maxDelayMs: config.maxDelayMs,
    execute: (event, context) => executorModule.executeEvent(event, context),
    ...(executorModule.isRetryableError ? { isRetryableError: executorModule.isRetryableError } : {}),
    onError: ({ stage, eventKey, error }) => {
      log('uaw_worker_error', {
        stage,
        eventKey: eventKey ?? null,
        code: safeCode(error, 'worker_error')
      });
    }
  });

  startupStage = 'worker_start';
  workerRun = worker.start();
  workerRun.catch(() => {}); // main awaits it; prevent a transient unhandled rejection race with signals.
  log('uaw_worker_started', {
    workerId: config.workerId,
    leaseMs: config.leaseMs,
    heartbeatMs: config.heartbeatMs,
    pollIntervalMs: config.pollIntervalMs,
    executorLoaded: true
  });
  await workerRun;
}

async function shutdown(signal) {
  if (shutdownPromise) return shutdownPromise;
  shutdownPromise = (async () => {
    if (worker) await worker.stop();
    if (pool) await pool.end();
    log('uaw_worker_stopped', { signal });
  })();
  return shutdownPromise;
}

for (const signal of ['SIGTERM', 'SIGINT']) {
  process.once(signal, () => {
    void shutdown(signal).catch(() => {
      log('uaw_worker_shutdown_failed', { signal });
      process.exitCode = 1;
    });
  });
}

try {
  await main();
} catch (error) {
  const startupDetails = startupStage === 'configuration'
    ? { reason: String(error?.message ?? 'invalid_configuration').slice(0, 240) }
    : { code: safeCode(error, 'startup_failed') };
  log('uaw_worker_startup_failed', { stage: startupStage, ...startupDetails });
  if (pool) {
    try { await pool.end(); } catch { /* preserve startup error status without exposing connection details */ }
  }
  process.exitCode = 1;
}