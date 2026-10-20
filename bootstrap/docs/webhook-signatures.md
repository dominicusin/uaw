# Provider-specific webhook signatures

Status checked: 2026-10-20. This is implementation guidance for the bundled reference receiver; no webhook subscriptions, public endpoints, or live provider connections were created.

## Built-in route factories

`src/webhooks/provider-routes.mjs` exports three route factories for `createWebhookServer()`:

```js
import { createWebhookServer } from '../src/webhook-server.mjs';
import {
  createGitHubWebhookRoute,
  createLinearWebhookRoute,
  createCalendlyWebhookRoute
} from '../src/webhooks/provider-routes.mjs';

const routes = [
  createGitHubWebhookRoute({ getSecret: () => secretStore.read('uaw/github/webhook-secret') }),
  createLinearWebhookRoute({ getSecret: () => secretStore.read('uaw/linear/webhook-secret') }),
  createCalendlyWebhookRoute({ getSecret: () => secretStore.read('uaw/calendly/webhook-secret') })
];
const server = createWebhookServer({ queue, routes });
```

Use distinct secrets for separate webhook registrations where the provider supports it. The example calls are inert until mounted by a host process; bind/listen, TLS termination, rate limits, firewall rules, logging, secret store and database pool are host responsibilities.

### GitHub

- Delivery ID: `X-GitHub-Delivery`.
- Signature header: `X-Hub-Signature-256`, format `sha256=<64 hex chars>`.
- Signed bytes: exact raw HTTP request body, HMAC-SHA256 with the webhook secret.
- There is no timestamp in this signature protocol. Deduplicate using the provider's delivery ID and the durable `(provider,event_id)` uniqueness key.
- The included test verifies GitHub's documented HMAC test vector.

Official docs: https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries

### Linear

- Delivery ID: `Linear-Delivery`.
- Signature header: `Linear-Signature`, a hex HMAC-SHA256 of the exact raw request body.
- Freshness headers/fields: `Linear-Timestamp` in Unix milliseconds and signed JSON `webhookTimestamp`; this route requires both to be fresh (default absolute skew <= 60 seconds) and within the configured skew of each other.
- The timestamp header itself is not incorporated into the HMAC input. Treat timestamp validation as an additional replay guard, not a replacement for signature verification and durable delivery-ID deduplication.

Official docs: https://linear.app/developers/webhooks

### Calendly

- Signature header: `Calendly-Webhook-Signature`, with `t=<Unix seconds>,v1=<hex HMAC>`.
- Signed bytes: UTF-8 timestamp, a literal `.` byte, then the exact raw HTTP request body.
- Timestamp freshness defaults to an absolute skew of <= 180 seconds.
- The bundled route derives the event key from SHA-256 of the exact raw request body because a universal delivery-ID header is not documented in the signature instructions. Exact-byte retries deduplicate; this is not a universal logical-event idempotency guarantee. If a trusted provider event identifier becomes available in a subscribed event envelope, prefer it via a reviewed route-specific `eventIdFromPayload`.

Official docs: https://developer.calendly.com/api-docs/overview/webhooks/webhook-signatures

## Why no universal provider route

Provider signature schemes are not interchangeable. The generic receiver accepts HMAC-SHA256 over the raw body. The provider-specific adapter only normalizes the official signature string and signed bytes; the queue still independently verifies HMAC before persisting the event. Timestamped providers must validate freshness before handing normalized signed bytes to the queue. Unknown schemes should fail closed and must not be approximated by signing re-serialized JSON.

Notion and the other catalogued integrations do not have a built-in webhook route in this iteration. Do not configure them through one of these three factories based on name similarity; first verify the applicable official protocol and add its own tests.

## Verification limits

The route tests are local HTTP contract tests around a fake queue. They validate signatures, timestamp rejection and idempotent retries without needing a provider account. They do not prove webhook subscriptions, real provider deliveries, TLS, reverse-proxy behavior, DB durability, or deployment-level clock synchronization. The PostgreSQL integration suite must run against the actual target database before production use.

## Runnable server configuration

`npm run start:webhooks` loads `scripts/serve-webhooks.mjs`. Required configuration: `UAW_DATABASE_URL`; `UAW_WEBHOOK_PROVIDERS=github,linear,calendly` (select only the needed providers); and the matching secret variable for each selected provider (`UAW_GITHUB_WEBHOOK_SECRET`, `UAW_LINEAR_WEBHOOK_SECRET`, `UAW_CALENDLY_WEBHOOK_SECRET`). `UAW_PORT` defaults to `8080`, `UAW_HOST` defaults to `127.0.0.1`; non-loopback bind is rejected unless `UAW_ALLOW_PUBLIC_BIND=1`. The runtime verifies that the queue schema is already installed and does not execute migrations. It needs the optional `pg` npm package. `/healthz` is process liveness; `/readyz` checks table presence and a bounded database query.