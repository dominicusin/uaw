# UAW integration status


Method: static inspection of all 80 Python files in `dominicusin/uaw` (working clone) plus grep for network clients, explicit mock markers and auth references.

| Group | Files | Status | Evidence |
|---|---|---|---|
| Adapter HTTP core | `adapters/base.py` | REAL transport helper | `aiohttp.ClientSession` at :245, `self._session.request` at :259; used by 8 adapter modules |
| Adapters: calendly, canva, figma, gamma, teams, vercel, wix | `adapters/*.py` | REAL-capable (credential-dependent) | import base, call request helpers; auth/token references present; no live call executed in this audit |
| Excalidraw adapter | `adapters/excalidraw_adapter.py` | MIXED | explicit `return a mock response` :424, `return mock data` :470, `Return mock JSON data` :485; other actions use base HTTP |
| GitHub integration | `integrations/github_integration.py` | EXTERNAL DEPENDENCY (unverified) | `_execute_tool` dynamically imports `github_app` module (:431-456); fails with IntegrationError if unavailable. No direct HTTP in repo |
| Linear integration | `integrations/linear_integration.py` | MOCK | `_execute_tool` :486-493 returns fixed `{"success": True, "data": {"message": ...}}` |
| Notion integration | `integrations/notion_integration.py` | MOCK | `_execute_tool` :509-512 marked "For now, return a mock response" |
| Box / Document Library integrations | `integrations/box_integration.py`, `document_library_integration.py` | MOCK | "For now, return a mock response" :432 / :328 |
| Asana / Calendar / Slack / Netlify integrations | `integrations/*.py` | UNVERIFIED STUB | no network client, no explicit mock marker, no auth references in file |
| Webhook server | `automation/webhook_server.py` | MOCK MODE | logs "Webhook server ready (mock mode)" :462 |

State layer (separate finding): `core/state_manager.py:77,93` and `core/uaw_core.py:186,210` read/write state via `json.dump` — no transaction, lock, or recovery. Idempotency mentioned only in `config/automation_config.py` and docs, not enforced in execution path.

Conclusion: UAW has real HTTP plumbing in adapters, but the GitHub/Linear/Notion control-plane integrations that the migration plan assumed are not live (GitHub requires an absent external module; Linear/Notion are mocks). Do not claim three live integrations. Next work: UAW-001/002 — capability registry with explicit real/mock/unsupported status, then transactional state and idempotency before any autonomy escalation.
