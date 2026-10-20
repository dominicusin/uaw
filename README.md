# Unified Agentic Workspace (UAW)

## 🚀 Unified Agentic Workspace - Единая интеллектуальная агентная система

**UAW** - это система для оркестрации работы Across 20+ сервисов (Microsoft Teams, Outlook, Google Calendar, Calendly, GitHub, Vercel, Netlify, Linear, Asana, Notion, Box, Gamma, Canva, Excalidraw, Figma, Wix) в единый рабочий процесс.

## 📋 Обзор проекта

### 🎯 Основная цель
Создание единой системы, которая позволяет:
- Получать запросы на естественном языке
- Автоматически планировать и выполнять операции через несколько сервисов
- Проверять результаты каждого этапа
- Формировать единый отчёт с прослеживаемыми связями между ресурсами

### 🏗️ Архитектура

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Unified Agentic Workspace (UAW)                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐          │
│  │  User Input   │    │   Event       │    │  Integration  │          │
│  │  (Natural     │    │  Ingestion    │    │   Registry    │          │
│  │   Language)   │───▶│               │───▶│              │          │
│  └──────────────┘    └──────────────┘    └──────────────┘          │
│          │                    │                    │                  │
│          ▼                    ▼                    ▼                  │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    Orchestrator Core                        │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │   │
│  │  │ Request       │  │ Workflow      │  │ Task          │    │   │
│  │  │ Parser        │  │ Engine        │  │ Orchestrator  │    │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘    │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                    │                                         │           │
│                    ▼                                         ▼           │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    Execution Layer                          │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │   │
│  │  │ MCP          │  │ REST          │  │ State         │    │   │
│  │  │ Integrations  │  │ Adapters      │  │ Manager       │    │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘    │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                    │                                         │           │
│                    ▼                                         ▼           │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    Data Layer                               │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │   │
│  │  │ Resource      │  │ Audit         │  │ Security      │    │   │
│  │  │ Mapper        │  │ Logger        │  │ Manager       │    │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘    │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

## 📦 Структура проекта

```
uaw/
├── core/                    # Ядро системы
│   ├── __init__.py          # Экспорты модуля
│   ├── uaw_core.py          # Центральный координатор
│   ├── state_manager.py     # Управление состоянием
│   ├── resource_mapping.py  # Сопоставление ресурсов
│   ├── security.py          # Безопасность (L0-L4)
│   └── audit.py             # Аудит и логирование
│
├── models/                  # Модели данных
│   ├── __init__.py          # Экспорты + MODEL_CLASSES
│   ├── base.py              # Базовые классы
│   ├── person.py            # Person
│   ├── team.py              # Team
│   ├── project.py           # Project
│   ├── task.py              # Task
│   ├── issue.py             # Issue
│   ├── repository.py        # Repository (Branch, Commit, PullRequest)
│   ├── deployment.py        # Deployment (BuildInfo, HealthCheck, TestResult)
│   ├── document.py          # Document (DocumentVersion, DocumentComment)
│   ├── event.py             # Event (Attendee, EventRecurrence)
│   ├── workflow.py          # Workflow (Step, Trigger, Condition, Action)
│   ├── integration.py       # Integration (Capability, RateLimit)
│   ├── approval.py          # Approval (Vote)
│   └── audit_event.py       # AuditEvent
│
├── integrations/            # MCP интеграции
│   ├── __init__.py
│   ├── base.py              # BaseIntegration
│   ├── registry.py          # IntegrationRegistry
│   ├── github_integration.py
│   ├── asana_integration.py
│   ├── calendar_integration.py
│   ├── slack_integration.py
│   ├── netlify_integration.py
│   ├── box_integration.py
│   ├── notion_integration.py
│   ├── linear_integration.py
│   └── document_library_integration.py
│
├── adapters/                # REST адаптеры
│   ├── __init__.py
│   ├── base.py
│   ├── teams_adapter.py
│   ├── calendly_adapter.py
│   ├── vercel_adapter.py
│   ├── gamma_adapter.py
│   ├── canva_adapter.py
│   ├── excalidraw_adapter.py
│   ├── figma_adapter.py
│   └── wix_adapter.py
│
├── orchestrator/            # Оркестратор
│   ├── __init__.py
│   ├── task_orchestrator.py
│   └── workflow_engine.py
│
├── automation/              # Автоматизация
│   ├── __init__.py
│   ├── event_manager.py
│   ├── webhook_server.py
│   ├── trigger.py
│   └── automation_engine.py
│
├── scenarios/               # Сценарии
│   ├── __init__.py
│   └── first_skvoznoy.py    # Первый сквозной сценарий
│
├── tests/                   # Тесты
│   ├── __init__.py
│   ├── test_core.py
│   ├── test_models.py
│   ├── test_scenarios.py
│   └── run_tests.py
│
├── docs/                    # Документация
│   ├── uaw_inventory_report.md
│   └── potential_capabilities_report.md
│
├── config/                  # Конфигурация (планируется)
└── utils/                   # Утилиты (планируется)
```

## 🔧 Установка и настройка

### Предварительные требования

- Python 3.11+
- asyncio
- dataclasses
- typing
- json

### Установка

```bash
# Клонирование репозитория
git clone <repository-url>
cd uaw

# Установка зависимостей (если есть)
pip install -r requirements.txt
```

### Настройка аутентификации

Для работы с MCP коннекторами требуется настроить OAuth2:

```python
from uaw.integrations.github_integration import GitHubIntegration

# Настройка токена
github = GitHubIntegration()
await github.authenticate(token="your-github-token")
```

## 🚀 Быстрый старт

### Пример использования

```python
import asyncio
from uaw.core.uaw_core import UAWCore
from uaw.scenarios.first_skvoznoy import execute_fix_bug_scenario

async def main():
    # Создание запроса на естественном языке
    request = """
    Исправь ошибку в проекте, создай issue, назначь исполнителя,
    подготовь исправление, прогони тесты, создай pull request,
    разверни preview, сообщи команде в Teams и организуй встречу
    """
    
    # Выполнение через UAW Core
    core = UAWCore()
    workflow = core.plan_workflow(request)
    
    # Или выполнение сквозного сценария
    report = await execute_fix_bug_scenario(
        project_name="my-project",
        bug_title="Fix login bug",
        bug_description="Users cannot login with special characters",
        assignee={
            "name": "John Doe",
            "github": "johndoe",
            "email": "john@example.com",
        },
        severity="high",
        priority="urgent",
    )
    
    print(report.to_markdown())

if __name__ == "__main__":
    asyncio.run(main())
```

## 📊 Поддерживаемые сервисы

### ✅ Подключенные (3)
- **GitHub** - Полная интеграция через MCP
- **Asana** - Полная интеграция через MCP
- **Document Library** - Внутренний сервис

### ⚠️ Доступные (требуют OAuth2) (12)
- Google Calendar
- Outlook Calendar
- Gmail
- Outlook
- Box
- Notion
- Linear
- Netlify
- Slack
- Slack HTTP
- SharePoint
- Google Drive

### ❌ Недоступные (имеются REST адаптеры) (8)
- Microsoft Teams
- Calendly
- Vercel
- Gamma
- Canva
- Excalidraw
- Figma
- Wix

## 🔐 Модель безопасности

UAW использует 5 уровней автономности:

| Уровень | Название | Описание |
|---------|---------|----------|
| L0 | Read Only | Только чтение и анализ |
| L1 | Prepare | Подготовка изменений |
| L2 | Supervised | Выполнение после подтверждения |
| L3 | Policy-Based | Автоматическое в рамках политики |
| L4 | Restricted | Чувствительные операции |

## 📋 Примеры запросов

### Сценарий 1: Исправление бага
```
"Исправь ошибку в проекте, создай issue, назначь исполнителя, подготовь исправление, 
прогони тесты, создай pull request, разверни preview, сообщи команде в Teams 
и организуй встречу для обсуждения результата"
```

### Сценарий 2: Создание задачи
```
"Создай задачу в Asana для проекта X, назначь её на John, установи приоритет высокий"
```

### Сценарий 3: Deployment
```
"Разверни новую версию приложения на Vercel из ветки main"
```

## 🧪 Тестирование

```bash
# Запуск всех тестов
python -m uaw.tests.run_tests

# Запуск тестов по категории
python -m uaw.tests.run_tests core
python -m uaw.tests.run_tests models
python -m uaw.tests.run_tests scenarios
```

## 📝 Документация

- [Отчёт об инвентаризации](docs/uaw_inventory_report.md)
- [Отчёт о возможностях](docs/potential_capabilities_report.md)

## 🤝 Вклад

1. Форкните репозиторий
2. Создайте ветку для вашей функции (`git checkout -b feature/your-feature`)
3. Закоммитьте изменения (`git commit -m 'Add some feature'`)
4. Запушьте в ветку (`git push origin feature/your-feature`)
5. Создайте Pull Request

## 📄 Лицензия

MIT License

## 📞 Контакты

**Автор**: Vibe Code (Mistral AI Agent)  
**Проект**: Unified Agentic Workspace (UAW)  
**Версия**: 1.0.0
