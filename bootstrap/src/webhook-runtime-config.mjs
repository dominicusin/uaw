import { createGitHubWebhookRoute, createLinearWebhookRoute, createCalendlyWebhookRoute } from './webhooks/provider-routes.mjs';

const LOCAL_HOSTS = new Set(['127.0.0.1', '::1', 'localhost']);
const PROVIDERS = Object.freeze({
  github: { secretName: 'UAW_GITHUB_WEBHOOK_SECRET', factory: createGitHubWebhookRoute },
  linear: { secretName: 'UAW_LINEAR_WEBHOOK_SECRET', factory: createLinearWebhookRoute },
  calendly: { secretName: 'UAW_CALENDLY_WEBHOOK_SECRET', factory: createCalendlyWebhookRoute }
});

function requiredEnv(env, name) {
  const value = env[name];
  if (typeof value !== 'string' || value.trim() === '') throw new Error(`${name} is required (value redacted)`);
  return value;
}

function parsePort(value) {
  if (value === undefined || value === '') return 8080;
  if (!/^\d+$/.test(String(value))) throw new Error('UAW_PORT must be an integer from 1 to 65535');
  const port = Number(value);
  if (!Number.isInteger(port) || port < 1 || port > 65535) throw new Error('UAW_PORT must be an integer from 1 to 65535');
  return port;
}

function validateDatabaseUrl(value) {
  let url;
  try { url = new URL(value); }
  catch { throw new Error('UAW_DATABASE_URL must be a valid PostgreSQL URL (value redacted)'); }
  if (!['postgres:', 'postgresql:'].includes(url.protocol) || !url.hostname || !url.pathname || url.pathname === '/') {
    throw new Error('UAW_DATABASE_URL must use postgres:// or postgresql:// and name a database (value redacted)');
  }
  return value;
}

/** Parse a safe, explicit runtime configuration without printing or echoing secret values. */
export function buildWebhookRuntimeConfig(env = process.env) {
  if (!env || typeof env !== 'object') throw new TypeError('env must be an environment-like object');
  const databaseUrl = validateDatabaseUrl(requiredEnv(env, 'UAW_DATABASE_URL'));
  const port = parsePort(env.UAW_PORT);
  const host = env.UAW_HOST?.trim() || '127.0.0.1';
  if (/[/\s\u0000-\u001f]/.test(host)) throw new Error('UAW_HOST is invalid');
  if (!LOCAL_HOSTS.has(host) && env.UAW_ALLOW_PUBLIC_BIND !== '1') {
    throw new Error('Non-loopback bind requires UAW_ALLOW_PUBLIC_BIND=1 and a trusted TLS/network edge');
  }
  const providerList = requiredEnv(env, 'UAW_WEBHOOK_PROVIDERS').split(',').map(name => name.trim().toLowerCase());
  if (providerList.some(name => !name) || new Set(providerList).size !== providerList.length) {
    throw new Error('UAW_WEBHOOK_PROVIDERS must be a comma-separated list without empty or duplicate entries');
  }
  const unknown = providerList.filter(name => !Object.hasOwn(PROVIDERS, name));
  if (unknown.length) throw new Error(`Unsupported provider route(s): ${unknown.join(', ')}`);
  const routes = providerList.map(provider => {
    const descriptor = PROVIDERS[provider];
    requiredEnv(env, descriptor.secretName);
    return descriptor.factory({
      getSecret: () => {
        const value = env[descriptor.secretName];
        if (typeof value !== 'string' || value.length === 0) throw new Error('secret_unavailable');
        return value;
      }
    });
  });
  return Object.freeze({ databaseUrl, host, port, providers: Object.freeze([...providerList]), routes: Object.freeze(routes) });
}