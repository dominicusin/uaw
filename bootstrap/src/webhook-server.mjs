import { createServer } from 'node:http';
import { TextDecoder } from 'node:util';

const utf8 = new TextDecoder('utf-8', { fatal: true });

class HttpError extends Error {
  constructor(status, code) {
    super(code);
    this.status = status;
    this.code = code;
  }
}

function requiredString(value, name) {
  if (typeof value !== 'string' || !value.trim() || /[\r\n\u0000-\u001f]/.test(value)) {
    throw new TypeError(`${name} must be a non-empty string without control characters`);
  }
  return value.trim();
}

function boundedInteger(value, name, min, max) {
  if (!Number.isInteger(value) || value < min || value > max) {
    throw new TypeError(`${name} must be an integer from ${min} to ${max}`);
  }
  return value;
}

function buildRouteMap(routes) {
  if (!Array.isArray(routes) || routes.length === 0) {
    throw new TypeError('routes must be a non-empty array');
  }
  const byPath = new Map();
  for (const input of routes) {
    const route = { ...input };
    route.path = requiredString(route.path, 'route.path');
    if (!route.path.startsWith('/') || route.path.includes('?') || route.path.includes('#') || route.path.includes('//')) {
      throw new TypeError('route.path must be an absolute, exact path without query/fragment');
    }
    route.provider = requiredString(route.provider, 'route.provider');
    route.eventIdHeader = requiredString(route.eventIdHeader, 'route.eventIdHeader').toLowerCase();
    route.signatureHeader = requiredString(route.signatureHeader, 'route.signatureHeader').toLowerCase();
    if (!/^[!#$%&'*+\-.^_`|~0-9a-z]+$/.test(route.eventIdHeader) ||
        !/^[!#$%&'*+\-.^_`|~0-9a-z]+$/.test(route.signatureHeader)) {
      throw new TypeError('route header names must be valid HTTP token names');
    }
    if (route.eventIdHeader === route.signatureHeader ||
        ['host', 'content-length', 'transfer-encoding', 'content-type'].includes(route.eventIdHeader) ||
        ['host', 'content-length', 'transfer-encoding', 'content-type'].includes(route.signatureHeader)) {
      throw new TypeError('route event/signature header names must be distinct and application-specific');
    }
    if (!(typeof route.secret === 'string' && route.secret.length > 0) && typeof route.getSecret !== 'function') {
      throw new TypeError('route must provide secret or getSecret()');
    }
    route.signaturePrefix ??= 'sha256=';
    if (typeof route.signaturePrefix !== 'string') throw new TypeError('route.signaturePrefix must be a string');
    route.maxAttempts = route.maxAttempts ?? 5;
    boundedInteger(route.maxAttempts, 'route.maxAttempts', 1, 100);
    if (byPath.has(route.path)) throw new TypeError(`duplicate webhook path: ${route.path}`);
    byPath.set(route.path, Object.freeze(route));
  }
  return byPath;
}

function jsonResponse(res, status, body, headers = {}) {
  if (res.headersSent || res.destroyed) return;
  const encoded = Buffer.from(JSON.stringify(body));
  res.writeHead(status, {
    'content-type': 'application/json; charset=utf-8',
    'content-length': encoded.length,
    'cache-control': 'no-store',
    'x-content-type-options': 'nosniff',
    ...headers
  });
  res.end(encoded);
}

function singleHeader(req, name) {
  const occurrences = [];
  for (let i = 0; i < req.rawHeaders.length; i += 2) {
    if (String(req.rawHeaders[i]).toLowerCase() === name) occurrences.push(req.rawHeaders[i + 1]);
  }
  if (occurrences.length !== 1) return null;
  const value = occurrences[0];
  if (typeof value !== 'string' || !value.trim() || /[\r\n\u0000]/.test(value)) return null;
  return value.trim();
}

async function readRawBody(req, maxBodyBytes) {
  const rawLength = req.headers['content-length'];
  if (rawLength !== undefined) {
    if (typeof rawLength !== 'string' || !/^\d+$/.test(rawLength)) {
      req.resume();
      throw new HttpError(400, 'invalid_content_length');
    }
    if (Number(rawLength) > maxBodyBytes) {
      req.resume();
      throw new HttpError(413, 'request_body_too_large');
    }
  }

  const chunks = [];
  let total = 0;
  return await new Promise((resolve, reject) => {
    let settled = false;
    const cleanup = () => {
      req.off('data', onData);
      req.off('end', onEnd);
      req.off('error', onError);
      req.off('aborted', onAborted);
    };
    const settleError = error => {
      if (settled) return;
      settled = true;
      cleanup();
      req.resume();
      reject(error);
    };
    const onData = chunk => {
      total += chunk.length;
      if (total > maxBodyBytes) {
        settleError(new HttpError(413, 'request_body_too_large'));
        return;
      }
      chunks.push(chunk);
    };
    const onEnd = () => {
      if (settled) return;
      settled = true;
      cleanup();
      resolve(Buffer.concat(chunks, total));
    };
    const onError = () => settleError(new HttpError(400, 'request_body_read_failed'));
    const onAborted = () => settleError(new HttpError(400, 'request_aborted'));
    req.on('data', onData);
    req.once('end', onEnd);
    req.once('error', onError);
    req.once('aborted', onAborted);
  });
}

function requestContentType(req) {
  const type = req.headers['content-type'];
  if (typeof type !== 'string') return false;
  return /^application\/json(?:\s*;\s*charset\s*=\s*(?:utf-8|utf8))?\s*$/i.test(type.trim());
}

/**
 * Create a small framework-free HTTP webhook ingress around a queue implementing ingestWebhook().
 * Route signatures are HMAC-SHA256 over the exact raw request bytes. Provider protocols that use a
 * different signing scheme must use a provider-specific verification adapter instead of this route.
 */
export function createWebhookServer({
  queue,
  routes,
  maxBodyBytes = 1_048_576,
  maxInFlight = 64,
  requestTimeoutMs = 15_000,
  headersTimeoutMs = 10_000,
  keepAliveTimeoutMs = 5_000,
  onError = () => {}
} = {}) {
  if (!queue || typeof queue.ingestWebhook !== 'function') {
    throw new TypeError('queue must implement ingestWebhook');
  }
  if (typeof onError !== 'function') throw new TypeError('onError must be a function');
  boundedInteger(maxBodyBytes, 'maxBodyBytes', 1, 50 * 1024 * 1024);
  boundedInteger(maxInFlight, 'maxInFlight', 1, 10_000);
  boundedInteger(requestTimeoutMs, 'requestTimeoutMs', 1_000, 300_000);
  boundedInteger(headersTimeoutMs, 'headersTimeoutMs', 1_000, requestTimeoutMs);
  boundedInteger(keepAliveTimeoutMs, 'keepAliveTimeoutMs', 1_000, 120_000);
  const routeMap = buildRouteMap(routes);
  let activeRequests = 0;

  async function report(stage, provider, code) {
    try { await onError({ stage, provider: provider ?? null, code: code ?? 'internal_error' }); }
    catch { /* Telemetry cannot break webhook handling. */ }
  }

  const server = createServer({
    requestTimeout: requestTimeoutMs,
    headersTimeout: headersTimeoutMs,
    keepAliveTimeout: keepAliveTimeoutMs,
    maxHeadersCount: 100
  }, (req, res) => {
    let released = false;
    activeRequests += 1;
    const release = () => {
      if (released) return;
      released = true;
      activeRequests = Math.max(0, activeRequests - 1);
    };
    res.once('finish', release);
    res.once('close', release);

    if (activeRequests > maxInFlight) {
      req.resume();
      jsonResponse(res, 503, { error: 'ingress_overloaded' }, { 'retry-after': '5', connection: 'close' });
      return;
    }

    void (async () => {
      let route;
      try {
        const url = new URL(req.url ?? '/', 'http://uaw.invalid');
        route = routeMap.get(url.pathname);
        if (!route) {
          req.resume();
          jsonResponse(res, 404, { error: 'not_found' });
          return;
        }
        if (req.method !== 'POST') {
          req.resume();
          jsonResponse(res, 405, { error: 'method_not_allowed' }, { allow: 'POST' });
          return;
        }
        if (!requestContentType(req)) {
          req.resume();
          jsonResponse(res, 415, { error: 'content_type_must_be_application_json' });
          return;
        }
        const encoding = req.headers['content-encoding'];
        if (encoding && encoding.toLowerCase() !== 'identity') {
          req.resume();
          jsonResponse(res, 415, { error: 'content_encoding_not_supported' });
          return;
        }

        const eventId = singleHeader(req, route.eventIdHeader);
        const signature = singleHeader(req, route.signatureHeader);
        if (!eventId || eventId.length > 200 || /[\u0000-\u001f\u007f]/.test(eventId)) {
          req.resume();
          jsonResponse(res, 400, { error: 'event_id_header_missing_or_invalid' });
          return;
        }
        if (!signature || signature.length > 256) {
          req.resume();
          jsonResponse(res, 401, { error: 'signature_missing_or_invalid' });
          return;
        }

        const rawBody = await readRawBody(req, maxBodyBytes);
        let payloadText;
        try { payloadText = utf8.decode(rawBody); }
        catch { throw new HttpError(400, 'request_body_must_be_utf8'); }
        try { JSON.parse(payloadText); }
        catch { throw new HttpError(400, 'request_body_must_be_json'); }

        let secret;
        try { secret = typeof route.getSecret === 'function' ? await route.getSecret() : route.secret; }
        catch {
          await report('secret_resolution', route.provider, 'secret_unavailable');
          jsonResponse(res, 503, { error: 'webhook_configuration_unavailable' }, { 'retry-after': '5' });
          return;
        }
        if (typeof secret !== 'string' || !secret) {
          await report('secret_resolution', route.provider, 'secret_unavailable');
          jsonResponse(res, 503, { error: 'webhook_configuration_unavailable' }, { 'retry-after': '5' });
          return;
        }

        const accepted = await queue.ingestWebhook({
          provider: route.provider,
          eventId,
          rawBody,
          signature,
          secret,
          signaturePrefix: route.signaturePrefix,
          maxAttempts: route.maxAttempts
        });
        jsonResponse(res, accepted.duplicate ? 200 : 202, {
          accepted: true,
          duplicate: accepted.duplicate === true,
          eventKey: accepted.event?.eventKey ?? null
        });
      } catch (error) {
        const status = error instanceof HttpError ? error.status
          : error?.code === 'webhook_signature_invalid' ? 401
          : error?.code === 'event_id_payload_mismatch' ? 409
          : 503;
        const code = error instanceof HttpError ? error.code
          : error?.code === 'webhook_signature_invalid' ? 'signature_invalid'
          : error?.code === 'event_id_payload_mismatch' ? 'event_id_payload_mismatch'
          : 'queue_unavailable';
        if (status === 503 || status === 409) await report('ingest', route?.provider, code);
        jsonResponse(res, status, { error: code }, status === 503 ? { 'retry-after': '5' } : {});
      }
    })().catch(async () => {
      await report('handler', null, 'unexpected_handler_error');
      jsonResponse(res, 500, { error: 'internal_error' });
    });
  });

  Object.defineProperty(server, 'activeWebhookRequests', { get: () => activeRequests });
  return server;
}