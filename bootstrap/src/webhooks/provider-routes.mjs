import { createHash } from 'node:crypto';

function signingSecret({ secret, getSecret }) {
  if (!(typeof secret === 'string' && secret.length > 0) && typeof getSecret !== 'function') {
    throw new TypeError('provide secret or getSecret()');
  }
  return secret === undefined ? { getSecret } : { secret };
}

function pathValue(path) {
  if (typeof path !== 'string' || !path.startsWith('/') || path.includes('?') || path.includes('#') || path.includes('//')) {
    throw new TypeError('path must be an exact absolute URL path');
  }
  return path;
}

function boundedSkew(value, name, fallback) {
  const result = value ?? fallback;
  if (!Number.isInteger(result) || result < 1_000 || result > 15 * 60_000) {
    throw new TypeError(`${name} must be an integer from 1000 to 900000`);
  }
  return result;
}

function invalidTimestamp() {
  const error = new Error('webhook_timestamp_invalid');
  error.code = 'webhook_timestamp_invalid';
  return error;
}

function withinSecondsWindow(timestampSeconds, nowMs, skewMs) {
  if (!Number.isSafeInteger(timestampSeconds) || timestampSeconds <= 0) return false;
  return Math.abs(nowMs - timestampSeconds * 1000) <= skewMs;
}

function withinMillisecondsWindow(timestampMs, nowMs, skewMs) {
  if (!Number.isSafeInteger(timestampMs) || timestampMs <= 0) return false;
  return Math.abs(nowMs - timestampMs) <= skewMs;
}

/** GitHub: X-Hub-Signature-256 is HMAC-SHA256(raw body), and X-GitHub-Delivery is the dedupe key. */
export function createGitHubWebhookRoute({ path = '/webhooks/github', secret, getSecret, maxAttempts = 5 } = {}) {
  return {
    path: pathValue(path), provider: 'github', ...signingSecret({ secret, getSecret }),
    eventIdHeader: 'x-github-delivery', signatureHeader: 'x-hub-signature-256',
    signaturePrefix: 'sha256=', maxAttempts
  };
}

/**
 * Linear: Linear-Signature is HMAC-SHA256(raw body); Linear-Delivery deduplicates delivery retries.
 * The timestamp is not added to the signed bytes. It is validated as a freshness/replay guard.
 */
export function createLinearWebhookRoute({ path = '/webhooks/linear', secret, getSecret,
  maxAttempts = 5, maxTimestampSkewMs = 60_000 } = {}) {
  const skew = boundedSkew(maxTimestampSkewMs, 'maxTimestampSkewMs', 60_000);
  return {
    path: pathValue(path), provider: 'linear', ...signingSecret({ secret, getSecret }),
    eventIdHeader: 'linear-delivery', signatureHeader: 'linear-signature', additionalHeaders: ['linear-timestamp'],
    signaturePrefix: '', maxAttempts,
    signatureAdapter({ rawBody, payload, headers, now }) {
      const timestampText = headers['linear-timestamp'];
      if (!/^\d{13}$/.test(timestampText ?? '')) throw invalidTimestamp();
      const timestamp = Number(timestampText);
      if (!withinMillisecondsWindow(timestamp, now, skew)) throw invalidTimestamp();
      // Linear documents webhookTimestamp in the signed JSON payload as an additional replay check.
      if (!payload || !Object.hasOwn(payload, 'webhookTimestamp') ||
          !withinMillisecondsWindow(payload.webhookTimestamp, now, skew) ||
          Math.abs(payload.webhookTimestamp - timestamp) > skew) throw invalidTimestamp();
      return { signature: headers['linear-signature'], signaturePrefix: '', signedPayload: rawBody };
    }
  };
}

/**
 * Calendly: Calendly-Webhook-Signature is `t=<seconds>,v1=<hex>`. HMAC input is UTF-8
 * `${t}.${rawBody}`. Payloads have no documented universal delivery-id header, so the exact raw-body
 * SHA-256 is used as an idempotency key; retries with the same bytes deduplicate durably.
 */
export function createCalendlyWebhookRoute({ path = '/webhooks/calendly', secret, getSecret,
  maxAttempts = 5, maxTimestampSkewMs = 180_000 } = {}) {
  const skew = boundedSkew(maxTimestampSkewMs, 'maxTimestampSkewMs', 180_000);
  return {
    path: pathValue(path), provider: 'calendly', ...signingSecret({ secret, getSecret }),
    signatureHeader: 'calendly-webhook-signature', signaturePrefix: '', maxAttempts,
    eventIdFromPayload({ rawBody }) {
      return `sha256:${createHash('sha256').update(rawBody).digest('hex')}`;
    },
    signatureAdapter({ rawBody, headers, now }) {
      const fields = new Map();
      for (const part of (headers['calendly-webhook-signature'] ?? '').split(',')) {
        const match = /^\s*([a-zA-Z0-9_]+)=([^,]+)\s*$/.exec(part);
        if (!match || fields.has(match[1])) throw invalidTimestamp();
        fields.set(match[1], match[2]);
      }
      const timestampText = fields.get('t');
      const signature = fields.get('v1');
      if (!/^\d{10}$/.test(timestampText ?? '') || !/^[a-f0-9]{64}$/i.test(signature ?? '')) {
        throw invalidTimestamp();
      }
      const timestamp = Number(timestampText);
      if (!withinSecondsWindow(timestamp, now, skew)) throw invalidTimestamp();
      return {
        signature,
        signaturePrefix: '',
        signedPayload: Buffer.concat([Buffer.from(`${timestampText}.`, 'utf8'), Buffer.from(rawBody)])
      };
    }
  };
}