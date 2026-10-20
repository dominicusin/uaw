"""
UAW Automation Examples
Примеры работы с системой автоматизации
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from uaw.automation.event_manager import EventManager, Event, EventType, EventSource
from uaw.automation.webhook_server import WebhookServer, WebhookConfig, WebhookProvider
from uaw.automation.trigger import TriggerManager, Trigger, TriggerType, TriggerCondition
from uaw.automation.automation_engine import AutomationEngine, Automation, AutomationRule


async def example_1_event_manager():
    """
    Пример 1: Работа с Event Manager
    """
    print("=" * 80)
    print("Пример 1: Event Manager")
    print("=" * 80)
    
    event_manager = EventManager()
    
    # Регистрация обработчика
    def handle_github_push(event: Event):
        print(f"Обработка GitHub push события: {event.payload.get('repository', {}).get('full_name')}")
    
    handler_id = event_manager.register_handler(
        event_type=EventType.GITHUB_PUSH,
        source=EventSource.GITHUB,
        callback=handle_github_push,
        filter_conditions={"ref": "refs/heads/main"},
        priority=10,
    )
    print(f"Зарегистрирован обработчик: {handler_id}")
    
    # Эмиссия события
    event = Event(
        event_id="",
        event_type=EventType.GITHUB_PUSH,
        source=EventSource.GITHUB,
        timestamp=datetime.utcnow(),
        payload={
            "ref": "refs/heads/main",
            "repository": {
                "full_name": "myorg/myrepo"
            },
            "commits": [
                {"id": "abc123", "message": "Fix login bug"}
            ]
        },
    )
    
    await event_manager.emit_event(event)
    print(f"Событие эмитировано: {event.event_id}")
    
    # Статистика
    stats = event_manager.get_stats()
    print(f"\nСтатистика:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    print()


async def example_2_webhook_server():
    """
    Пример 2: Работа с Webhook Server
    """
    print("=" * 80)
    print("Пример 2: Webhook Server")
    print("=" * 80)
    
    webhook_server = WebhookServer()
    
    # Регистрация webhook
    webhook_id = webhook_server.register_webhook(
        provider=WebhookProvider.GITHUB,
        endpoint="/webhooks/github",
        secret="my-secret-key",
        events=["push", "pull_request", "issues"],
    )
    print(f"Зарегистрирован webhook: {webhook_id}")
    
    # Получение конфигурации
    config = webhook_server.get_webhook_config(webhook_id)
    if config:
        print(f"\nКонфигурация webhook:")
        print(f"  Провайдер: {config.provider.value}")
        print(f"  Endpoint: {config.endpoint}")
        print(f"  События: {config.events}")
    
    # Проверка подписи
    handler = webhook_server.handlers.get(WebhookProvider.GITHUB)
    if handler:
        payload = b'{"action": "opened", "number": 123}'
        signature = "sha256=abc123"  # В реальности это правильная подпись
        is_valid = handler.verify_signature(payload, signature)
        print(f"\nПроверка подписи: {'✅ Валидно' if is_valid else '❌ Невалидно'}")
    
    # Статистика
    stats = webhook_server.get_stats()
    print(f"\nСтатистика:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    print()


async def example_3_trigger_manager():
    """
    Пример 3: Работа с Trigger Manager
    """
    print("=" * 80)
    print("Пример 3: Trigger Manager")
    print("=" * 80)
    
    trigger_manager = TriggerManager()
    
    # Создание триггера
    trigger = Trigger(
        trigger_id=f"trigger:{datetime.utcnow().timestamp()}",
        name="GitHub Push Trigger",
        trigger_type=TriggerType.WEBHOOK,
        webhook_id="webhook-123",
        event_type=EventType.GITHUB_PUSH,
        event_source=EventSource.GITHUB,
        conditions=[
            TriggerCondition(
                condition_id="cond-1",
                field="ref",
                operator="eq",
                value="refs/heads/main"
            )
        ],
        actions=[
            {
                "action_type": "workflow",
                "target": "workflow:deploy-on-push",
                "parameters": {}
            }
        ],
        is_enabled=True,
        priority=10,
    )
    
    trigger_manager.register_trigger(trigger)
    print(f"Зарегистрирован триггер: {trigger.trigger_id}")
    
    # Получение триггера
    retrieved = trigger_manager.get_trigger(trigger.trigger_id)
    print(f"Триггер извлечен: {retrieved is not None}")
    
    # Список всех триггеров
    all_triggers = trigger_manager.list_triggers()
    print(f"\nВсего триггеров: {len(all_triggers)}")
    
    # Проверка условий
    test_data = {"ref": "refs/heads/main"}
    for condition in trigger.conditions:
        result = condition.evaluate(test_data)
        print(f"Условие '{condition.field}' {condition.operator} '{condition.value}': {'✅' if result else '❌'}")
    print()


async def example_4_scheduled_trigger():
    """
    Пример 4: Планируемый триггер
    """
    print("=" * 80)
    print("Пример 4: Scheduled Trigger")
    print("=" * 80)
    
    trigger_manager = TriggerManager()
    
    # Создание планируемого триггера (каждый день в 9:00)
    trigger = Trigger(
        trigger_id=f"trigger:scheduled-{datetime.utcnow().timestamp()}",
        name="Ежедневная проверка",
        trigger_type=TriggerType.SCHEDULED,
        schedule="0 9 * * *",  # Каждый день в 9:00 UTC
        timezone="UTC",
        conditions=[],
        actions=[
            {
                "action_type": "workflow",
                "target": "workflow:daily-check",
                "parameters": {}
            }
        ],
        is_enabled=True,
        priority=5,
    )
    
    trigger_manager.register_trigger(trigger)
    print(f"Зарегистрирован планируемый триггер: {trigger.trigger_id}")
    print(f"Расписание: {trigger.schedule}")
    print(f"Часовой пояс: {trigger.timezone}")
    
    # Получение времени следующего выполнения
    next_time = trigger.get_next_execution_time()
    if next_time:
        print(f"Следующее выполнение: {next_time}")
    print()


async def example_5_automation_engine():
    """
    Пример 5: Работа с Automation Engine
    """
    print("=" * 80)
    print("Пример 5: Automation Engine")
    print("=" * 80)
    
    automation_engine = AutomationEngine()
    await automation_engine.initialize()
    
    # Создание автоматизации
    automation_id = await automation_engine.create_automation(
        name="Автоматическое развертывание",
        description="Автоматическое развертывание при push в main",
        triggers=[
            Trigger(
                trigger_id=f"trigger:{datetime.utcnow().timestamp()}",
                name="GitHub Push to Main",
                trigger_type=TriggerType.WEBHOOK,
                webhook_id="webhook-123",
                event_type=EventType.GITHUB_PUSH,
                event_source=EventSource.GITHUB,
                conditions=[
                    TriggerCondition(
                        condition_id="cond-1",
                        field="ref",
                        operator="eq",
                        value="refs/heads/main"
                    )
                ],
                actions=[
                    {
                        "action_type": "workflow",
                        "target": "workflow:deploy",
                        "parameters": {"environment": "staging"}
                    }
                ],
            )
        ],
        is_enabled=True,
    )
    
    print(f"Создана автоматизация: {automation_id}")
    
    # Получение автоматизации
    automation = automation_engine.get_automation(automation_id)
    if automation:
        print(f"\nИнформация об автоматизации:")
        print(f"  Название: {automation.name}")
        print(f"  Описание: {automation.description}")
        print(f"  Включена: {automation.is_enabled}")
        print(f"  Триггеры: {len(automation.triggers)}")
    
    # Список всех автоматизаций
    all_automations = automation_engine.list_automations()
    print(f"\nВсего автоматизаций: {len(all_automations)}")
    print()


async def example_6_automation_rule():
    """
    Пример 6: Создание правила автоматизации
    """
    print("=" * 80)
    print("Пример 6: Automation Rule")
    print("=" * 80)
    
    # Создание правила автоматизации
    rule = AutomationRule(
        rule_id=f"rule:{datetime.utcnow().timestamp()}",
        name="Правило для критических issue",
        description="Автоматическое уведомление при создании критического issue",
        trigger=Trigger(
            trigger_id=f"trigger:{datetime.utcnow().timestamp()}",
            name="Critical Issue Trigger",
            trigger_type=TriggerType.EVENT,
            event_type=EventType.GITHUB_ISSUE,
            event_source=EventSource.GITHUB,
            conditions=[
                TriggerCondition(
                    condition_id="cond-1",
                    field="labels",
                    operator="contains",
                    value="critical"
                )
            ],
        ),
        conditions=[
            {
                "type": "severity_check",
                "field": "severity",
                "operator": "eq",
                "value": "critical"
            }
        ],
        actions=[
            {
                "action_type": "notification",
                "target": "teams:dev-team",
                "parameters": {
                    "message": "Создан критический issue!",
                    "type": "critical"
                }
            }
        ],
        is_enabled=True,
        priority=1,
    )
    
    print(f"Создано правило автоматизации: {rule.rule_id}")
    print(f"Название: {rule.name}")
    print(f"Описание: {rule.description}")
    print(f"Включено: {rule.is_enabled}")
    print(f"Приоритет: {rule.priority}")
    print()


async def example_7_event_driven_automation():
    """
    Пример 7: Event-driven автоматизация
    """
    print("=" * 80)
    print("Пример 7: Event-Driven Automation")
    print("=" * 80)
    
    # Создание цепочки: Событие -> Триггер -> Автоматизация
    
    # 1. Событие
    event = Event(
        event_id="",
        event_type=EventType.GITHUB_PULL_REQUEST,
        source=EventSource.GITHUB,
        timestamp=datetime.utcnow(),
        payload={
            "action": "opened",
            "number": 123,
            "pull_request": {
                "title": "Fix login bug",
                "state": "open",
                "url": "https://github.com/org/repo/pull/123"
            },
            "repository": {
                "full_name": "org/repo"
            }
        },
    )
    
    print(f"Событие: {event.event_type.value}")
    print(f"  Действие: {event.payload.get('action')}")
    print(f"  PR: {event.payload.get('pull_request', {}).get('title')}")
    print()
    
    # 2. Триггер
    trigger = Trigger(
        trigger_id=f"trigger:pr-{datetime.utcnow().timestamp()}",
        name="PR Review Trigger",
        trigger_type=TriggerType.EVENT,
        event_type=EventType.GITHUB_PULL_REQUEST,
        event_source=EventSource.GITHUB,
        conditions=[
            TriggerCondition(
                condition_id="cond-1",
                field="action",
                operator="eq",
                value="opened"
            )
        ],
        actions=[
            {
                "action_type": "workflow",
                "target": "workflow:review-pr",
                "parameters": {}
            }
        ],
    )
    
    print(f"Триггер: {trigger.name}")
    print(f"  Условия: {len(trigger.conditions)}")
    print(f"  Действия: {len(trigger.actions)}")
    print()
    
    # 3. Проверка соответствия
    matches = trigger.matches_event(event)
    print(f"Событие соответствует триггеру: {'✅' if matches else '❌'}")
    print()


async def example_8_webhook_to_workflow():
    """
    Пример 8: Цепочка Webhook -> Event -> Workflow
    """
    print("=" * 80)
    print("Пример 8: Webhook to Workflow Chain")
    print("=" * 80)
    
    # Создание компонентов
    webhook_server = WebhookServer()
    event_manager = EventManager()
    
    # Регистрация webhook
    webhook_id = webhook_server.register_webhook(
        provider=WebhookProvider.GITHUB,
        endpoint="/webhooks/github",
        secret="my-secret",
        events=["push"],
    )
    
    # Регистрация обработчика в Event Manager
    def handle_push(event: Event):
        print(f"Обработка push события: {event.payload.get('repository', {}).get('full_name')}")
        # В реальности здесь запускался бы workflow
    
    event_manager.register_handler(
        event_type=EventType.GITHUB_PUSH,
        source=EventSource.GITHUB,
        callback=handle_push,
        filter_conditions={"ref": "refs/heads/main"},
    )
    
    print(f"Цепочка настроена:")
    print(f"  1. Webhook: {webhook_id}")
    print(f"  2. Event Manager: обработчик зарегистрирован")
    print(f"  3. Workflow: будет запущен при событии")
    print()
    
    # Симуляция webhook запроса
    payload = b'{"ref": "refs/heads/main", "repository": {"full_name": "org/repo"}}'
    headers = {
        "X-GitHub-Event": "push",
        "X-Hub-Signature-256": "sha256=abc123"
    }
    
    # В реальности это обрабатывалось бы HTTP сервером
    print("Симуляция webhook запроса:")
    print(f"  Payload: {payload.decode()}")
    print(f"  Headers: {headers}")
    print()


async def run_automation_example():
    """Запуск всех примеров автоматизации"""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 22 + "UAW AUTOMATION EXAMPLES" + " " * 26 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    
    examples = [
        ("Event Manager", example_1_event_manager),
        ("Webhook Server", example_2_webhook_server),
        ("Trigger Manager", example_3_trigger_manager),
        ("Scheduled Trigger", example_4_scheduled_trigger),
        ("Automation Engine", example_5_automation_engine),
        ("Automation Rule", example_6_automation_rule),
        ("Event-Driven Automation", example_7_event_driven_automation),
        ("Webhook to Workflow", example_8_webhook_to_workflow),
    ]
    
    for name, example in examples:
        print(f"→ {name}...")
        try:
            await example()
            print(f"✅ {name} выполнен\n")
        except Exception as e:
            print(f"❌ {name} не выполнен: {e}\n")
    
    print("=" * 80)
    print("Все примеры автоматизации выполнены!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_automation_example())
