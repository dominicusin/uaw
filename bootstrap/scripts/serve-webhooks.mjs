import { buildWebhookRuntimeConfig } from '../src/webhook-runtime-config.mjs';
import { createPostgresEventQueue } from '../src/postgres-event-queue.mjs';
import { createWebhookServer } from '../src/webhook-server.mjs';

let pool;
let server;
let shuttingDown = false;
let shutdownPromise;

async function assertSchema(dbPool) {
  const result = await dbPool.query({
    text: `SELECT to_regclass('public.uaw_event_inbox') AS inbox,
                  to_regclass('public.uaw_event_attempts') AS attempts,
                  to_regclass('public.uaw_event_sources') AS sources`,
    query_timeout: 3_000
  });
  const row = result.rows?.[0];
  if (!row?.inbox || !row?.attempts || !row?.sources) {
    throw new Error('Required UAW queue tables are missing; apply schemas/postgres-event-inbox.sql with the migration role');
  }
}

async function main() {
  const config = buildWebhookRuntimeConfig();
  let pg;
  try { pg = await import('pg'); }
  catch { throw new Error('Optional dependency "pg" is not installed; install it in the host runtime'); }
  const Pool = pg.Pool ?? pg.default?.Pool;
  if (typeof Pool !== 'function') throw new Error('Installed "pg" package does not export Pool');
  pool = new Pool({ connectionString: config.databaseUrl, max: 10, connectionTimeoutMillis: 5_000,
    idleTimeoutMillis: 30_000, application_name: 'uaw-webhook-ingress' });
  await assertSchema(pool);
  const queue = createPostgresEventQueue({ pool });
  server = createWebhookServer({
    queue,
    routes: config.routes,
    readinessCheck: async () => {
      if (shuttingDown) throw new Error('draining');
      await assertSchema(pool);
      await pool.query({ text: 'SELECT 1', query_timeout: 3_000 });
    },
    onError: ({ stage, provider, code }) => {
      process.stderr.write(`${JSON.stringify({ event: 'uaw_webhook_error', stage, provider, code })}\n`);
    }
  });
  await new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(config.port, config.host, resolve);
  });
  process.stdout.write(`${JSON.stringify({ event: 'uaw_webhook_server_listening', host: config.host,
    port: config.port, providers: config.providers, healthPath: '/healthz', readinessPath: '/readyz' })}\n`);
}

async function shutdown(signal) {
  if (shutdownPromise) return shutdownPromise;
  shuttingDown = true;
  shutdownPromise = (async () => {
    if (server?.listening) {
      const forceClose = setTimeout(() => server.closeAllConnections?.(), 15_000);
      forceClose.unref();
      await new Promise((resolve, reject) => server.close(error => error ? reject(error) : resolve()));
      clearTimeout(forceClose);
    }
    if (pool) await pool.end();
    process.stdout.write(`${JSON.stringify({ event: 'uaw_webhook_server_stopped', signal })}\n`);
  })();
  return shutdownPromise;
}

for (const signal of ['SIGTERM', 'SIGINT']) {
  process.once(signal, () => {
    void shutdown(signal).catch(() => {
      process.stderr.write(`${JSON.stringify({ event: 'uaw_shutdown_failed', signal })}\n`);
      process.exitCode = 1;
    });
  });
}

function safeStartupReason(error) {
  let reason = String(error?.message ?? 'startup_failed');
  for (const key of ['UAW_DATABASE_URL', 'UAW_GITHUB_WEBHOOK_SECRET', 'UAW_LINEAR_WEBHOOK_SECRET', 'UAW_CALENDLY_WEBHOOK_SECRET']) {
    const value = process.env[key];
    if (typeof value === 'string' && value.length > 0) reason = reason.split(value).join('[REDACTED]');
  }
  reason = reason.replace(/postgres(?:ql)?:\/\/[^\s@]+@/gi, 'postgresql://[REDACTED]@');
  return reason.slice(0, 400);
}

try {
  await main();
} catch (error) {
  process.stderr.write(`${JSON.stringify({ event: 'uaw_webhook_startup_failed', reason: safeStartupReason(error) })}\n`);
  if (pool) {
    try { await pool.end(); } catch { /* preserve original startup failure */ }
  }
  process.exitCode = 1;
}