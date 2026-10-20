# Unified Agentic Workspace — отчёт об инвентаризации и потенциальных возможностях

**Дата проверки:** 19 октября 2026 г.  
**Область:** инструменты текущего runtime, безопасные операции чтения, существующие объекты UAW в Notion/Linear и возможность пройти первый сквозной сценарий.  
**Принцип доказательности:** наличие операции в каталоге не означает, что авторизация, разрешения и успешность реального вызова подтверждены.

## 1. Итог

В runtime каталоге обнаружено **2 368 действий в 196 группах инструментов**. Это количество зарегистрированных действий, а не подтверждение авторизации каждой интеграции. Значительная часть требуемых систем уже имеет специализированные коннекторы; повторно реализовывать их с нуля не нужно.

В среде уже есть зачаток UAW:

- [Notion UAW Home](https://app.notion.com/p/3fe25978644381d99622dd4562db1ce5?pvs=204) — обзор рабочей среды.
- [Notion UAW Resources](https://app.notion.com/p/9683937bcaa445a6862ac61c7d18f3b6?pvs=204) — существующая база ресурсов.
- [Notion UAW Tasks](https://app.notion.com/p/830eceb11f3f43f094e95a6cfce35aeb?pvs=204) — доска задач.
- [Linear DOM-5](https://linear.app/dominicusin/issue/DOM-5/uaw-bootstrap-unified-agentic-workspace-foundation) — существующая задача-основание, на момент проверки статус **Backlog**.
- Существует запись workflow `demo-001`, но её страница Notion не содержит тела процесса. Описание DOM-5 указывает на чтение и подготовку, а не на подтверждённый цикл Issue → PR → Deploy → Notification. Сквозной сценарий **не считается пройденным**.

Главные препятствия: не найден доступный для записи репозиторий именно UAW; Teams API-запрос к списку команд падает с `AADSTS500014`; Outlook Calendar API возвращает `MailboxNotEnabledForRESTAPI`; источник событий Automations недоступен для проверки.

## 2. Матрица целевых интеграций

`connected` — существенный безопасный read-запрос успешно отработал; `partial` — подключение частично работает или ключевая функция заблокирована; `read_only` — подтверждены только чтения и нет проверенной записи; `unauthorised` — авторизация явно отклонена; `unavailable` — отдельный коннектор не обнаружен.

| Сервис | Действий в каталоге | Состояние | Фактические наблюдения |
|---|---:|---|---|
| Microsoft Teams | 38 | `partial` | `get_profile` успешен. `list_teams` возвращает `AADSTS500014`: service principal ресурса отключён; отправка сообщений не тестировалась. |
| Outlook Calendar | 34 | `partial` | Профиль отвечает, но `list_calendars` и `get_mailbox_settings` возвращают `MailboxNotEnabledForRESTAPI`. Проверка свободных слотов/создание событий заблокированы. |
| Outlook Email | 48 | `partial` | Профиль подтвердился; есть инструменты поиска, чтения, черновиков и отправки, но операции с письмами не выполнялись. |
| Google Calendar | 0 | `unavailable` | Отдельного коннектора нет. Есть opt-in mock-tested REST-заготовка FreeBusy/Events с UAW-keyed create/verification; нужны реальные OAuth scopes, paging/sync lifecycle и live read-after-write tests. |
| Calendly | 0 | `unavailable` | Отдельного коннектора нет. Официальный API поддерживает event-type/scheduled-event reads и webhook subscriptions; локальная заготовка mock-tested, но токен, required scopes и реальный endpoint ещё не подключены. |
| GitHub | 89 | `connected` | `get_profile` и `list_repositories` успешны. Каталог содержит операции issues, branches, commits, PR, reviews, Actions и логов; записи в ходе аудита не выполнялись. |
| Vercel | 235 | `connected` | Пользователь авторизован, `list_projects` вернул 4 проекта; поиск проекта UAW — 0 результатов. Deploy не запускался. |
| Netlify | 0 | `unavailable` | Коннектора нет. Подготовлена mock-tested REST-заготовка чтения Sites/Deploys и проверки commit + HTTP health; нужны scoped token/site ID и live contract tests. |
| Linear | 74 | `connected` | Workspace, команда `DOM` и issue `DOM-5` успешно прочитаны. У issue статус `Backlog`; мутации в этом аудите не выполнялись. |
| Asana | 27 | `partial` | `get_me` и `get_teams` успешны; найдена команда `IT`. `get_projects` вернул пустой список, premium `search_tasks` ответил `payment_required` — поиск ограничен тарифом. |
| Notion | 40 | `connected` | Найдены и прочитаны UAW Home, UAW Resources и UAW Tasks, в том числе схема базы. Инструменты создания/изменения доступны, записи проверяются отдельно. |
| Box | 49 | `connected` | `who_am_i` вернул активного пользователя; `search_files_keyword(UAW)` вернул 0 совпадений без ошибки. Каталог включает чтение, загрузку версий, метаданные и комментарии. |
| Gamma | 21 | `connected` | `get_gammas` вернул существующий документ `Gamma Tips & Tricks`. Генерация/редактирование/экспорт не запускались. |
| Canva | 40 | `connected` | Поиск отработал без ошибки, но дизайнов по `UAW` не найдено. Права на изменения дизайна не проверялись. |
| Excalidraw | 0 | `unavailable` | Hosted-коннектора нет. Локальный mock-independent helper проверяет и сериализует нативную `.excalidraw` JSON-сцену; загрузка/синхронизация assets с hosted-сервисом не реализована. |
| Figma | 48 | `connected` | `whoami` успешен: план Starter, Full seat, роль admin; Figma AI доступен, `specs_enabled=false` и Code Layers выключены. Изменение файла не проверялось. |
| Wix | 31 | `connected` | `get_profile`, `ListWixSites`, `GetSiteContext` успешны. Найден `allunity`, Published, Free plan, Velo выключен; установлены Wix Blog, Bookings, Events & Tickets, Forms & Payments и другие приложения. Коммерческие записи не проверялись. |
| Automations | 7 | `partial` | `list` и `peek` возвращают **0** системных расписаний. `list_event_sources` недоступен (`Action not found`). Страницы с именами автоматизаций в Notion не доказывают, что webhooks реально исполняются. |

**GitHub target:** поиск обнаружил `cstuncsik/unified-agentic-workspace`, но это чужой репозиторий, доступный только на чтение (`pull=true`, `admin=false`). Среди собственных доступных репозиториев не найден `dominicusin/unified-agentic-workspace`. Существующий репозиторий сайта нельзя использовать для UAW без явного технического основания.

## 3. Что подтверждено чтением

1. GitHub: собственный профиль и список репозиториев доступны.
2. Vercel: чтение профиля и четырёх проектов доступно; ни один из найденных проектов не совпал с UAW.
3. Linear: [DOM-5](https://linear.app/dominicusin/issue/DOM-5/uaw-bootstrap-unified-agentic-workspace-foundation) существует и остаётся в Backlog.
4. Notion: рабочие страницы UAW и база ресурсов существуют. Ограничение схемы `UAW Resources`: `Service` содержит только `[Linear, GitHub, Notion, Vercel, Netlify, Teams, UAW]`; `Status` — `[Backlog, Active, Blocked, Done]`; `Type` — `[Workflow, Project, Issue, PullRequest, Document, Deployment, Automation, Repository]`. Это не универсальный каталог всех провайдеров без расширения.
5. Wix: обнаружен реальный опубликованный сайт `allunity` по адресу https://dominicusin.wixsite.com/website; контекст сайта доступен, но это не подтверждает права на конкретные операции платежей/заказов.
6. Figma, Canva, Gamma и Box отвечают на безопасные read/search запросы; реальные write/публикации не тестировались.

## 4. Архитектура UAW

`Connectors/APIs → Integration Registry → Event Ingestion → Durable Queue → Workflow Orchestrator → Adapter Execution → Verification → Audit Log → Notification`

- **Integration Registry:** состояние авторизации, операции, scopes, квоты, пагинация, события, метод проверки результата и ошибки.
- **Common Resource Model:** стабильный `uawId`, тип, ссылки провайдеров, `systemOfRecord`, отношения и происхождение. UAW не должен заменять исходные provider objects.
- **Identity/Policy:** разрешения на уровне `user × integration × operation × workflow × environment`; L0–L4 не назначаются глобально.
- **Orchestrator:** граф зависимостей (DAG), параллельность независимых шагов, состояния, pause/resume и ожидание approval.
- **Event ingestion/queue:** короткий обработчик события, дедупликация, очереди, bounded retry/backoff, echo guard и восстановление.
- **Verification:** API acceptance не означает success. Каждый шаг получает `succeeded` только с доказательством (ID/URL/статус/CI checks/HTTP health response).
- **Audit:** actor, integration, operation, inputs hash, response reference, approval ID, retries, timestamps и evidence; секреты/конфиденциальные payload не записываются.

### Предлагаемые системы-источники истины

| Ресурс | Источник истины | Что хранит UAW |
|---|---|---|
| Код, ветки, commits, PR, reviews, Actions | GitHub | provider IDs/URLs, связи и статус-кэш |
| Issue | Linear для Linear issue; Asana для Asana task | внутренний ID, внешняя ссылка и связи без дублирования исходных полей |
| Документ и UAW-граф | Notion для страниц/отношений; Box для файлов/версий | ссылки, provenance, версии и связи |
| Calendar Event | система, где событие создано | общий ID + provider ID и статус |
| Deployment | Vercel или Netlify | deployment ID, commit, environment, verification result |
| Wix CMS/orders/bookings | соответствующий Wix API | ссылки и минимально необходимые проекции |
| Workflow/Approval/AuditEvent | UAW | авторитетное состояние исполнения и подтверждений |

Идентификация: внешний объект — `(integration, externalId)`; событие — `(integration, eventId)`; шаг — `(workflowId, stepId)`. Не зеркалировать событие обратно в источник без echo guard. Мутации должны выполнять preflight/desired-state check и read-after-write verification.

## 5. Первый сквозной сценарий

План: `GitHub repo/read → Linear issue → branch/file change → tests/Actions → PR → Vercel preview → deploy verification → Notion report → Teams notification → calendar meeting (optional)`.

**Фактически пройдено:** discovery/read репозиториев и проектов; чтение DOM-5; чтение UAW Home/Resources/Tasks; каталогизация коннекторов.

**Заблокировано:**

- Нет найденного собственного write-capable репозитория UAW для безопасной ветки/PR.
- Teams `list_teams` падает с `AADSTS500014`, поэтому канал уведомлений не подтверждён.
- Outlook Calendar не отдаёт список календарей из-за `MailboxNotEnabledForRESTAPI`.
- В этом прогоне не создавались PR/commit/deployment, не запускались тесты проекта и health-check.
- Реальные event triggers Automations не подтверждены: список автоматизаций пуст, event-source action недоступен.

Итог сквозного сценария — **`blocked` / `partially_implemented`**, не `completed`. Не менялись production-ресурсы, не создавались PR, не запускался deployment, не отправлялись реальные приглашения/сообщения.

## 6. Безопасность

- **L0:** чтение и анализ.
- **L1:** подготовка планов/diff/черновиков без внешней публикации.
- **L2:** внешняя операция после явного approval с точным target и operation.
- **L3:** только заранее разрешённые сочетания actor/integration/operation/workflow/environment, с лимитами объёма и частоты.
- **L4:** production promotion/rollback, удаление, секреты, опасные миграции, платежи/возвраты и чувствительные персональные данные — отдельное подтверждение и аудит.

Текст внешних документов, issue или почты не может менять политику UAW. Production deploy, merge и публикации запрещено включать в общий L3 без отдельной scoped-политики.

## 7. Приоритетный план

### P0 — разблокировать первый сценарий

1. Починить Teams consent/service principal; проверить `list_teams`, channels и только затем тестовое сообщение в согласованном канале.
2. Исправить Exchange mailbox/API enablement или подключить другой календарь; проверить calendars/free-busy/timezone и тестовое событие.
3. Подключить собственный write-capable репозиторий UAW. Не использовать чужой `cstuncsik/unified-agentic-workspace` и не записывать код UAW в репозиторий сайта наугад.
4. Определить host/runtime для backend и durable state. Путь `/home/workdir/artifacts/uaw/`, упомянутый в Linear/Notion, отсутствует в текущей файловой среде.

### P1 — минимальное ядро

5. [x] Расширить Notion `UAW Resources` для всех целевых интеграций: состояния, capabilities, system-of-record, evidence URL, last-verified date и autonomy level. Дальше добавить provider-specific schema/version/provenance при выборе persistence backend.
6. Реализовать event inbox, dedupe ledger, долговременное состояние workflow, DAG scheduler, approvals и read-after-write verification.
7. Сделать реальный вертикальный срез GitHub → Linear → Notion; Teams добавить после восстановления авторизации.
8. Проверить PR без merge и Vercel preview без promotion в production.

### P2 — отдельные адаптеры

9. Google Calendar: подключить OAuth credentials, доработать paging/sync token/watch lifecycle и провести live smoke tests для FreeBusy/Event read-after-write.
10. Calendly: подключить минимальные scopes, обработать webhook signing/receiver, подтвердить subscription и тестовое событие.
11. Netlify: подключить scoped token/site ID, пройти live Sites/Deploys/readiness/health-check; build trigger сам по себе не доказывает успех.
12. Excalidraw: при необходимости добавить хранение/публикацию scene + assets; текущий helper только сохраняет редактируемый JSON, hosted sync отсутствует.

### P3 — зрелая эксплуатация

13. Webhooks источников, где они реально доступны; polling с курсорами и лимитами для остальных.
14. Contract tests на 401/403, 404, 429, timeout, duplicate event, conflict, stale write, failed verification и resume-after-restart.
15. Единая панель/чат-представление для approval queue, статусов, зависимостей, ошибок и аудита.

## 8. Статусы приёмки

| Критерий | Статус | Основание |
|---|---|---|
| Инвентаризация интеграций | `partially_implemented` | Каталог и некоторые reads подтверждены; не все scopes/quotas/webhooks исследованы. |
| Единая модель ресурсов | `partially_implemented` | Notion UAW Resources существует, но схема ограничена. |
| Межсервисная оркестрация | `partially_implemented` | Существуют DOM-5 и описания workflow, но исполняемый end-to-end цикл не доказан. |
| Идемпотентность в подключённом runtime | `not_started` | Нет подтверждённого event inbox/ledger. В bootstrap-пакете есть тестируемая reference logic. |
| Восстановление после перезапуска в production | `not_started` | Нет работающего production worker/queue; локальное файловое сохранение не заменяет распределённую систему. |
| Календарь/таймзоны | `blocked` | Outlook mailbox API заблокирован; Google Calendar/Calendly не подключены. |
| CI/deployment/health checks | `partially_implemented` | GitHub/Vercel инструменты доступны, но тестовый deploy и health-check не запускались. |
| Автоматизации | `blocked` | Native Automations пуст; event-source listing недоступен. |
| Безопасная автономность | `partially_implemented` | Policy helpers и тесты включены в пакет; реальные внешние операции ещё не заведены под общий policy engine. |
| Сквозной сценарий | `blocked` | Нет собственного UAW write repo, Teams blocker и Outlook Calendar blocker. |

## 9. Официальные ссылки для будущих адаптеров

- Google Calendar FreeBusy: https://developers.google.com/workspace/calendar/api/v3/reference/freebusy/query
- Calendly API/auth: https://developer.calendly.com/docs/getting-started/introduction
- Calendly webhooks: https://developer.calendly.com/api-docs/calendly-api/webhooks/create-webhook-subscription
- Netlify API: https://docs.netlify.com/api-and-cli-guides/api-guides/get-started-with-api/
- Netlify build hooks: https://docs.netlify.com/build/configure-builds/build-hooks/
- Excalidraw export: https://docs.excalidraw.com/docs/%40excalidraw/excalidraw/api/utils/export
- Excalidraw JSON scene utilities: https://docs.excalidraw.com/docs/%40excalidraw/excalidraw/api/utils

## 10. Ограничения

Это снимок доступного runtime, а не полный администраторский аудит аккаунтов. Не все квоты, scopes, webhook subscriptions и write permissions проверены. Не запускались destructive/financial actions, внешние PR/deployments, публикации, реальные сообщения или приглашения. Факт присутствия действия отдельно от фактически проверенного успеха.


## 11. Continued autonomous work — implementation checkpoint

### Live Notion/Linear changes

- Created and fetched back the audit page: https://app.notion.com/p/3fe25978644381bd9443f9a201503efb?pvs=204
- Extended `UAW Resources` with integration state, capability markers, system-of-record, evidence URL, verification date and default autonomy level; extended service and object-type enumerations.
- Created 18 integration catalog records and verified that a query returned 18 integration rows. Every provider record defaults to L0; catalog presence is not treated as verified write permission.
- Fetched back `demo-001` and confirmed `Status=Blocked`.
- Added an audit comment to Linear DOM-5 (comment ID `1c0aec65-b2e5-4c45-87a7-516fffbc3f40`) and called `list_comments` to verify it exists.
- Added tasks for the calendar blocker, dedicated UAW repository, durable orchestrator, GitHub → Linear → Notion slice, Vercel Preview verification, and Automations event triggers. The existing Microsoft Teams re-authentication task was reused instead of duplicated.

### Local reference core

- Added `src/executor.mjs`: dependency-layer runner with concurrency limit, explicit operation classes, adapter preflight, exact scope matching for policies/approvals, bounded transient-error retries with exponential backoff, persisted transitions, mandatory verification evidence and reconcile-before-repeat.
- Added a guard so verification errors after accepted side effects do not trigger automatic mutation retries.
- Added `src/adapters/README.md` with explicit adapter contracts and constraints; no fake adapters or credentials were introduced.
- Added tests for concurrent independent DAG steps, dependency ordering, approval scope mismatch, transient retry limits across resumes, missing operation classifications, and verification failure without re-executing a mutation.
- Fresh verification: `npm test` — **18 passed, 0 failed**; `npm run validate` — **18 integrations, 9 connected, 5 partial, 4 unavailable**. This proves local reference logic only, not production durability or provider API execution.

### Still not implemented in the connected environment

The reference runner is not a distributed queue. Opt-in REST adapter examples exist for Google Calendar, Calendly and Netlify, plus the Excalidraw scene helper, but they are not connected to production credentials. No real GitHub issue/branch/PR, Vercel/Netlify deployment, Teams message or calendar event was created. Those steps remain blocked pending repository ownership and connector repair.


## 12. Автономная реализация после первоначального аудита

### Новые локальные REST-адаптеры

- `src/adapters/providers/google-calendar.mjs`: FreeBusy, чтение событий, `uawId`-дедупликация при создании, детерминированный event ID, read-after-write verification.
- `src/adapters/providers/calendly.mjs`: текущий пользователь, типы событий, запланированные события, просмотр и создание webhook subscription по явному вызову. Секрет подписи/приёмник webhook и реальная booking-операция не реализованы.
- `src/adapters/providers/netlify.mjs`: Sites/Deploys, чтение deployment и отдельная проверка готовности, ожидаемого commit и HTTP health endpoint. Build trigger и production promotion намеренно не добавлены.
- `src/adapters/providers/excalidraw.mjs`: проверка формата и сериализация нативной редактируемой сцены; это не подключение к размещённому сервису Excalidraw.

Адаптеры принимают внедряемые токены и `fetchImpl`. Их тесты используют mock HTTP-ответы. Они **не** переведены в состояние `connected`, не тестировались на реальных аккаунтах и требуют подключения секретов/разрешений через официальный OAuth/API или безопасный host bridge.

### Свежая проверка

- `npm test`: **54 пройден, 0 провален**. В тесты входят DAG/policy/executor/state-store и mock-тесты четырёх provider-модулей.
- `npm run validate`: **18 интеграций**, распределение реестра: 9 `connected`, 5 `partial`, 4 `unavailable`.
- Эти результаты подтверждают локальную эталонную логику и валидацию реестра, но не production-runtime, не реальные внешние API и не end-to-end workflow.

### Обновлённое фактическое состояние внешних систем

- Notion UAW Resources содержит 18 записей Integration и дополнительные поля для состояния подключения, capabilities, источника истины, доказательной ссылки, даты проверки и допустимого уровня автономности. Новые задачи записаны в UAW Tasks.
- `demo-001` подтверждён повторным чтением со статусом `Blocked`.
- Комментарии аудита добавлены к Linear DOM-5 и прочитаны через `list_comments`.
- Не создавались GitHub commit/PR, Vercel/Netlify deployment, production-публикация, Teams сообщение или приглашение календаря. Главные блокеры прежние: отсутствует найденный owned write-capable UAW repo, Teams выдаёт `AADSTS500014`, Outlook Calendar — `MailboxNotEnabledForRESTAPI`, Automations event source недоступен и нативный список Automations пуст.

**Вывод:** подготовлена расширенная, локально протестированная база для следующей итерации, но UAW как долговременно работающая production-система пока не реализована. Сквозной сценарий остаётся `blocked`; это намеренно отражено в Notion и `workflow-demo-001.json`.


## 13. Дополнительная итерация — API-адаптеры

**Свежая проверка локального пакета:** `npm test` — 46 тестов пройдены, 0 ошибок; `npm run validate` — реестр валиден: 18 интеграций (9 connected, 5 partial, 4 unavailable).

Добавлены официальные opt-in API-адаптеры:
- `src/adapters/providers/github.mjs` — чтение репозитория/веток/commit/issues/PR/Actions, создание issue с UAW-маркером, создание только draft PR и отдельная проверка PR. Адаптер не предоставляет merge/push.
- `src/adapters/providers/linear.mjs` — GraphQL, viewer/teams/issue/search, создание issue с UAW-маркером, обработка GraphQL ошибок даже при HTTP 200 и read-after-write verification.
- `src/adapters/providers/vercel.mjs` — project/deployment reads и независимая Preview-проверка commit + HTTPS health check. Не создаёт, не отменяет и не продвигает deployment.
- `src/adapters/providers/notion.mjs` — Notion API `2026-03-11`, поиск страниц, создание строки data source или дочерней страницы с UAW ID в заголовке и проверка повторным чтением.

Все тесты этих адаптеров используют mock HTTP; это **не** подтверждает живую API-авторизацию. Поиск существующего объекта перед записью ограничивает дубли, но не гарантирует exactly-once между несколькими независимыми процессами; для production нужна durable per-key lease/unique constraint.

Сквозной workflow `demo-001` остаётся `Blocked`: нет подтверждённого собственного write-capable репозитория UAW, Teams возвращает `AADSTS500014`, Outlook Calendar — `MailboxNotEnabledForRESTAPI`, источники событий Automations недоступны. Никаких production writes, merge или deployment в этой итерации не запускалось.


## 14. Event-ingestion reference

В `src/event-inbox.mjs` добавлен отдельный reference-модуль для приёма событий: проверка HMAC-SHA256 по исходному телу запроса; дедупликация по `(provider,eventId)` и защита от повторного ID с изменённым body; file-backed журнал; lease на обработку; подтверждение завершения только с `verified=true` и `evidenceRef`; ограниченные повторы с экспоненциальной задержкой; pause/resume; dead-letter при исчерпании попыток или падении worker на последней попытке; базовая редактирующая фильтрация секретов в тексте ошибки.

**Свежая проверка (20 октября):** `npm test` — 54 пройденных теста, 0 ошибок; `npm run validate` проходит. Это reference-библиотека, не поднятый webhook-server и не multi-host queue. Она не включает провайдерские webhook subscriptions/routes или автоматическое подключение к Automations; для production необходимо добавить provider-specific signature parsing, HTTP endpoints, транзакционный event store/lease и dead-letter уведомления. UAW `demo-001` по-прежнему `Blocked`.


## 15. Финальная проверка этой итерации

После добавления защиты Vercel Preview verifier (обязательный ожидаемый commit, allow-list host, запрет health-запроса к production/неизвестному target) и тестов event-inbox recovery, свежая локальная проверка (20 октября): **54 passed, 0 failed**; validation реестра по-прежнему проходит (18 integrations: 9 connected, 5 partial, 4 unavailable).

Event inbox дополнительно проверяет, что worker, умерший на последней попытке, переводится в dead-letter после истечения lease, а не повторяется бесконечно; строки ошибок фильтруют bearer/API-key/secret-подобные значения. Store остаётся single-process, и payload должен быть минимизирован/редактирован до сохранения. Сквозной workflow `demo-001` не запускался повторно, потому что внешние блокеры не изменились.


## 16. Live GitHub/Linear remediation checkpoint — 2026-10-20

The external read probes uncovered a real accessibility regression in `dominicusin/dominicusin.github.io`: Playwright run [#811](https://github.com/dominicusin/dominicusin.github.io/actions/runs/39237259486) reported four `label-content-name-mismatch` failures for `#search-button`. The pinned Blowfish theme uses a nested `search:` translation map; site locale files previously used a dotted scalar override, so the theme string `Поиск (/)` remained. The button also visibly shows `⌘K` while that string does not.

A narrow draft PR is now open: [#451 — align Blowfish search aria-label with shortcut hint](https://github.com/dominicusin/dominicusin.github.io/pull/451). It changes only `i18n/ru.yaml` and `i18n/en.yaml`, switches to nested search locale maps, and adds the visible `⌘K` shortcut to the accessible name. PR remains draft and unmerged.

- Quality CI run #497 passed.
- License Check #534 passed; Dependency Review #327 passed.
- Playwright E2E run #814 completed successfully: **28 tests passed**. Quality CI #497, License Check #534 and Dependency Review #327 also passed. DOM-7 remains In Review because PR #451 is a draft and remains unmerged.
- Vercel Preview for the PR commit again reports `BUILD_FAILED / Resource provisioning failed`; event/log retrieval is blocked by connector scope 403, tracked in [Linear DOM-6](https://linear.app/dominicusin/issue/DOM-6/investigate-vercel-build-failed-resource-provisioning-failed). The Vercel project metadata says `live=false`; repo production uses GitHub Pages, so there is no evidence the Vercel error caused the public site to be down.
- Fix tracking: [Linear DOM-7](https://linear.app/dominicusin/issue/DOM-7/fix-blowfish-search-button-override-causing-axe-accessible-name). The UAW `demo-001` workflow remains `Blocked`; this separate PR is not an end-to-end UAW run.

No merge to `main` or production deployment was performed.


## Additional implementation checkpoint — 2026-10-20 (PostgreSQL event queue)

Implemented a PostgreSQL-backed event-queue reference in `src/postgres-event-queue.mjs` and `schemas/postgres-event-inbox.sql`, documented in `docs/postgres-event-queue.md`. It provides provider/event uniqueness, exact-raw-byte HMAC-SHA256 ingress for the normalized `sha256=<hex>` contract, payload digest mismatch handling, transactional `FOR UPDATE SKIP LOCKED` claim, fencing lease tokens, attempt audit, retry/backoff, pause/resume, dead-letter listing and redrive without reusing attempt numbers. The existing file inbox was also corrected to authenticate and hash byte-array requests without UTF-8 normalization.

Fresh `npm test`: **65 passed, 0 failed, 1 skipped**. The skipped opt-in PostgreSQL integration test requires `UAW_TEST_DATABASE_URL` and the optional `pg` package. The current environment has no `psql`, PostgreSQL server or Docker executable; therefore this is mock/contract evidence only, not live database validation. `npm run validate` passes: 18 integration records (9 connected, 5 partial, 4 unavailable). No live webhook endpoint, database, production worker or provider credential was provisioned.

Remaining gates: execute the opt-in integration suite against the deployment's actual PostgreSQL version and least-privilege runtime role; add provider-specific signature decoders/HTTP routes; and connect the durable queue to a host runtime plus the policy-checked executor.


## 17. Durable event queue hardening — 2026-10-20

The PostgreSQL event queue now uses the database clock for leases and settlement timestamps by default, so claim/completion/failure decisions in ordinary multi-worker mode do not depend on synchronized worker-host clocks. Each claim uses a new fencing token; the attempt audit records lease expiry before an event is reclaimed. Dead-letter redrive retains lifetime attempt history and expands the retry budget rather than resetting attempt numbers. Exact raw-byte HMAC validation/hashing is covered in both the single-process reference inbox and PostgreSQL ingress.

**Fresh check:** `npm run check` succeeded: **65 passed, 0 failed, 1 skipped**; registry validation is still 18 integrations (9 connected, 5 partial, 4 unavailable). The one skipped test is the opt-in live PostgreSQL integration suite. There is no configured `UAW_TEST_DATABASE_URL`, optional Node package `pg`, or PostgreSQL server in this environment, so database-level concurrency/permissions are not claimed verified. The suite now separates migration/admin access (`UAW_TEST_DATABASE_URL`) from the runtime role (`UAW_TEST_RUNTIME_DATABASE_URL`); with different roles it asserts that the runtime role cannot create schema objects, delete events or truncate the inbox.

A durable task was added to Notion to run that integration suite with the target PostgreSQL major version and least-privilege runtime role: [Run PostgreSQL event-queue integration tests against the target runtime](https://app.notion.com/p/3ff2597864438162afd8f32731608563?pvs=204).

The queue is still an adapter, not a live service: no HTTP webhook server, persistent production database, worker process or provider subscription was provisioned. `demo-001` remains `Blocked`.

## 18. Worker lease heartbeat — 2026-10-20

Added `queue.extendLease({ eventKey, workerId, leaseToken, leaseMs, now? })` to the PostgreSQL queue. A renewal is accepted only while the event is still `processing`, the owner and fencing token match, and the existing lease has not expired. Deadline extension uses the database clock by default and `GREATEST` so a heartbeat cannot accidentally shorten an already-longer lease. The attempt-history deadline is updated in the same transaction; a missing audit row causes rollback instead of silently diverging queue state. The optional real-PostgreSQL suite now tests renewal preventing premature reclaim, expiry/reclaim fencing and stale completion rejection.

**Fresh validation:** `npm run check` passes with **67 passed, 0 failed, 1 skipped**. The skipped test is the opt-in PostgreSQL integration suite; no live database is present in this environment, so real transaction and multi-worker guarantees remain unverified here. The integration test is extended but has only been syntax-checked and skipped locally. Registry validation remains 18 integrations (9 connected, 5 partial, 4 unavailable).

**Runtime safety note:** a rejected heartbeat is not cancellation of a provider call already in flight. A worker must stop starting further work and reconcile potentially applied mutations before replay. No database, webhook server, long-running worker or real provider action was provisioned; UAW workflow `demo-001` remains `Blocked`.



## 2026-10-20 — PostgreSQL worker runner

Added `src/postgres-worker.mjs`, a single-event-at-a-time runner that composes with the durable PostgreSQL queue. It renews leases while an injected policy-checked executor runs, passes an `AbortSignal`, stops settlement after lease loss, requires independent verified result evidence before success, applies retry classification to known execution errors, avoids a second settlement after ambiguous database completion, and supports graceful stop that interrupts idle polling. Seven dedicated mock-contract tests pass.

Latest local checks: 74 passed, 0 failed, 1 skipped; registry remains 18 integrations (9 connected, 5 partial, 4 unavailable). The opt-in live PostgreSQL integration suite remains skipped because no disposable database and DB test credentials are configured. The runner is a reference primitive, not a deployed daemon: HTTP ingress, production executor wiring and live provider credentials are still absent; `demo-001` remains Blocked.

## 19. HTTP webhook ingress — 2026-10-20

Added `src/webhook-server.mjs`, a framework-free Node.js HTTP receiver around the PostgreSQL queue contract. It uses explicit exact-path route allow-lists; validates POST/content type/UTF-8 JSON; rejects compressed bodies and duplicate/missing event/signature headers; applies a configurable body ceiling, request/header timeouts and in-flight backpressure; passes untouched request bytes into the queue's HMAC-SHA256 validator; acknowledges deduplicated provider deliveries; and returns sanitized generic errors without writing payloads, signatures, secrets or raw exception messages to logs/responses. Route secrets can be resolved lazily from a host secret manager. `docs/postgres-event-queue.md` now includes example wiring and hard deployment boundaries.

Ten local HTTP tests cover raw-byte forwarding, idempotent delivery, invalid HMAC, size/content-type/UTF-8/JSON rejection, missing and duplicated headers, route/method isolation, event ID/body mismatch, generic queue/storage failure handling, secret resolution failure and in-flight backpressure.

**Fresh `npm run check` at this historical checkpoint: 84 passed, 0 failed, 1 skipped (85 total);** `npm run validate` passes for 18 integrations (9 connected, 5 partial, 4 unavailable). The only skip remains the opt-in real-PostgreSQL suite; local ingress tests use a fake queue and do not establish live DB durability or cross-host behavior. The HTTP receiver is code in the bootstrap package, not an internet-facing deployment. At this historical checkpoint, provider-specific signatures (including timestamp/replay rules) remained outstanding; the next checkpoint adds three provider route factories. Subscriptions, TLS/edge policy, live database and policy-checked executor deployment remain outstanding. `demo-001` remains `Blocked`.


## 20. Provider-specific webhook signature adapters — 2026-10-20

Added `src/webhooks/provider-routes.mjs` with route factories for GitHub, Linear and Calendly. GitHub accepts the documented `X-Hub-Signature-256` HMAC of exact raw bytes and deduplicates via `X-GitHub-Delivery`. Linear verifies `Linear-Signature` over exact raw bytes and enforces freshness for both `Linear-Timestamp` and the signed JSON `webhookTimestamp`. Calendly verifies the documented `t=<seconds>,v1=<hex>` header over `${timestamp}.${rawBody}` and applies a default 180-second freshness window. The durable queue now allows the provider adapter to supply signed bytes and still performs independent HMAC verification before insertion.

Five new provider route tests cover acceptance/deduplication, stale timestamps, malformed config and GitHub's official HMAC test vector. Fresh local result: 90 tests total, 89 passed, 0 failed, 1 skipped; registry validation remains 18 integrations (9 connected, 5 partial, 4 unavailable). The skipped test remains live PostgreSQL integration. These tests are local HTTP tests using a fake queue, not live provider deliveries. Calendly uses an exact-raw-body hash as a dedupe fallback because the signature guidance does not document a universal delivery ID; logical event identity should replace this where an authoritative event identifier is available. Notion and other providers remain without routes until their official schemes are separately verified.

Official documentation reviewed: GitHub https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries ; Linear https://linear.app/developers/webhooks ; Calendly https://developer.calendly.com/api-docs/overview/webhooks/webhook-signatures. Live HTTP deployment, provider subscriptions, TLS/edge configuration, real database integration and policy-checked executor wiring remain unconfigured; UAW `demo-001` is still `Blocked`.


## 21. Provider-specific signatures and runnable ingress — 2026-10-20

Added `src/webhooks/provider-routes.mjs`: documented GitHub raw-body HMAC with `X-GitHub-Delivery` idempotency, Linear raw-body HMAC plus timestamp freshness checks over `Linear-Timestamp` and signed-body `webhookTimestamp`, and Calendly's `t + '.' + rawBody` HMAC input with a 180-second default absolute freshness window. `verifyHmacSha256` and the PostgreSQL queue now support separate `signedPayload` bytes while the queue persists/hashes the original raw body. The GitHub documented HMAC test vector passes. Calendly uses raw-body SHA-256 as a deduplication fallback because the signature guide does not document a universal delivery ID; this deduplicates exact-byte retries only. Notion and other providers deliberately remain without route factories.

Added a fail-closed runtime config parser, `scripts/serve-webhooks.mjs` (`npm run start:webhooks`), liveness `/healthz`, database-backed readiness `/readyz`, bounded DB probes, preflight that refuses to start when required queue tables are missing, structured redacted logs and graceful SIGTERM/SIGINT shutdown. Runtime enables only explicitly selected GitHub/Linear/Calendly routes, requires the matching secret, defaults to loopback binding, and refuses non-loopback binding without explicit `UAW_ALLOW_PUBLIC_BIND=1`. It requires optional `pg` installed in the host runtime and a pre-applied migration; startup has not been run against a live PostgreSQL instance.

Five provider route tests and seven runtime configuration tests plus two health/readiness tests were added. Latest `npm run check`: **99 tests total, 98 passed, 0 failed, 1 skipped**; registry validation passed: 18 integrations (9 connected, 5 partial, 4 unavailable). The one skip remains the real PostgreSQL suite. The local tests use fake queue / config only and do not establish production DB behavior or live webhook connectivity. Official protocol references: GitHub https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries ; Linear https://linear.app/developers/webhooks ; Calendly https://developer.calendly.com/api-docs/overview/webhooks/webhook-signatures. UAW `demo-001` remains `Blocked`.

## 22. End-to-end HTTP → queue contract → worker path — 2026-10-20

Added `test/webhook-worker.e2e.test.mjs` and `npm run test:e2e`. The scenario brings up the real Node HTTP ingress on an ephemeral loopback port, signs a GitHub delivery over the original body bytes, verifies the route accepts one delivery (`202`), resends the identical event and verifies dedupe (`200`), then runs `createPostgresWorker` against a queue-contract double and requires verified result evidence before the event becomes `succeeded`. It asserts the executor was called exactly once even after the duplicate delivery. The double checks the HMAC and models the minimum queue interface needed by ingress/worker.

This is an end-to-end **contract** test, not a real PostgreSQL end-to-end test: the queue double does not prove transaction isolation, `FOR UPDATE SKIP LOCKED`, recovery after database/network failure, or runtime-role grants. An attempt to refresh this container's APT package metadata to install PostgreSQL timed out; no PostgreSQL server/client or `pg` Node package is installed. The opt-in live PostgreSQL integration test therefore remains skipped and must not be considered passed.

Fresh `npm run check`: **100 tests total, 99 passed, 0 failed, 1 skipped**; registry validation passes for 18 integration records (9 connected, 5 partial, 4 unavailable). `npm run test:e2e`: 1 passed, 0 failed. Provider signature/runtime behavior, queue contract, worker, HTTP server, schemas and deployment files are included in the artifact, but there is still no running DB-backed ingress or worker service, no live provider subscriptions, and no production executor/credentials. `demo-001` remains `Blocked`.


## 23. Separately runnable worker process — 2026-10-20

Added `src/worker-runtime-config.mjs`, `scripts/run-worker.mjs` (`npm run start:worker`), `test/worker-runtime-config.test.mjs` and `docs/worker-runtime.md`. The entry point requires a PostgreSQL URL, unique explicit worker identity and absolute host-owned executor module path. It validates lease/heartbeat/poll/retry configuration, opens a bounded `pg` pool, preflights the three queue tables in `public`, imports only the explicitly configured local JavaScript module, and requires an `executeEvent(event, { signal, workerId, leaseToken })` export. It optionally accepts a host `isRetryableError` classifier. Structured logs expose stage/code identifiers, not DB URLs, passwords or exception messages. SIGTERM/SIGINT stop new work, await the active execution/settlement and close the pool. The executor must provide its own network deadlines, policy/approval enforcement, and independent read-after-write verification; no universal business executor is bundled.

Five runtime config tests plus a process-level fail-closed smoke test were added. Current `npm run check`: **107 tests total, 106 passed, 0 failed, 1 skipped**; `npm run test:e2e`: **1 passed**; validation remains 18 integrations (9 connected, 5 partial, 4 unavailable). Startup smoke test verifies missing `UAW_DATABASE_URL` returns failure without exposing credential-bearing URLs or configured private paths. The local HTTP→queue-contract→worker E2E still uses an in-memory double. PostgreSQL server/client and the optional Node `pg` package are absent; APT metadata refresh timed out. As a result, no real DB transaction/concurrency/least-privilege integration run occurred and the worker/ingress were not deployed. `demo-001` remains `Blocked`.


## 24. CI workflow for the live PostgreSQL queue test — 2026-10-20

Added `.github/workflows/ci.yml` to run on pushes, pull requests and manual dispatch. It provisions a PostgreSQL 16 service container with a health check, installs exact `pg@8.23.1` into the ephemeral runner, creates a distinct `uaw_runtime` login, and executes `npm run check` with separate migration/admin and runtime database URLs. Because the existing opt-in test detects `UAW_TEST_DATABASE_URL`, that command is intended to run the live database integration instead of skipping it. A separate E2E contract run follows. Workflow permissions are restricted to `contents: read`, the job has a 15-minute timeout, and concurrency cancels superseded runs. Added three static tests to assert the important workflow guardrails and `docs/ci.md` with the service/role model.

The workflow has **not** been executed on GitHub from this generated artifact. Local registry access timed out while trying to obtain `pg`, and there is no local PostgreSQL server/client in this environment, so live DB behavior still has no passing evidence. Do not represent the proposed CI job as executed.

Fresh local verification after adding CI config tests: `npm run check` — **110 tests, 109 passed, 0 failed, 1 skipped**; registry validation passes for 18 integrations (9 connected, 5 partial, 4 unavailable); `npm run test:e2e` — 1 passed. All source/script/test syntax checks passed. The skipped item is the real PostgreSQL integration suite; the local E2E continues to use an in-memory queue-contract double. `demo-001` remains `Blocked`.