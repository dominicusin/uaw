"""
UAW Integration Examples
Примеры работы с интеграциями и адаптерами
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional

from uaw.integrations.github_integration import GitHubIntegration
from uaw.integrations.asana_integration import AsanaIntegration
from uaw.integrations.linear_integration import LinearIntegration
from uaw.integrations.calendar_integration import CalendarIntegration
from uaw.integrations.netlify_integration import NetlifyIntegration
from uaw.integrations.box_integration import BoxIntegration

from uaw.adapters.teams_adapter import MicrosoftTeamsAdapter
from uaw.adapters.vercel_adapter import VercelAdapter
from uaw.adapters.calendly_adapter import CalendlyAdapter


async def example_1_github_integration():
    """
    Пример 1: Работа с GitHub интеграцией
    """
    print("=" * 80)
    print("Пример 1: GitHub Integration")
    print("=" * 80)
    
    github = GitHubIntegration()
    
    # Проверка подключения
    status = await github.check_health()
    print(f"Статус подключения: {status}")
    
    # Получение информации о интеграции
    print(f"\nИнформация об интеграции:")
    print(f"  Название: {github.name}")
    print(f"  Сервис: {github.service}")
    print(f"  Статус: {github.status.value}")
    print(f"  Базовый URL: {github.base_url}")
    
    # Получение списка возможностей
    capabilities = github.get_capabilities()
    print(f"\nВозможности ({len(capabilities)}):")
    for cap in capabilities[:5]:  # Показываем первые 5
        print(f"  - {cap.name} ({cap.method} {cap.endpoint})")
    print(f"  ... и еще {len(capabilities) - 5} возможности")
    
    # Проверка rate limits
    rate_limits = github.get_rate_limits()
    if rate_limits:
        print(f"\nRate Limits:")
        for limit in rate_limits:
            print(f"  {limit.endpoint}: {limit.limit} запросов/{limit.period_seconds} сек")
    print()


async def example_2_asana_integration():
    """
    Пример 2: Работа с Asana интеграцией
    """
    print("=" * 80)
    print("Пример 2: Asana Integration")
    print("=" * 80)
    
    asana = AsanaIntegration()
    
    # Проверка подключения
    status = await asana.check_health()
    print(f"Статус подключения: {status}")
    
    # Получение информации
    print(f"\nИнформация об интеграции:")
    print(f"  Название: {asana.name}")
    print(f"  Сервис: {asana.service}")
    print(f"  Статус: {asana.status.value}")
    
    # Возможности
    capabilities = asana.get_capabilities()
    print(f"\nКлючевые возможности:")
    for cap in capabilities[:5]:
        print(f"  - {cap.name}")
    print()


async def example_3_linear_integration():
    """
    Пример 3: Работа с Linear интеграцией
    """
    print("=" * 80)
    print("Пример 3: Linear Integration")
    print("=" * 80)
    
    linear = LinearIntegration()
    
    # Проверка подключения
    status = await linear.check_health()
    print(f"Статус подключения: {status}")
    
    # Информация
    print(f"\nИнформация об интеграции:")
    print(f"  Название: {linear.name}")
    print(f"  Сервис: {linear.service}")
    print(f"  Статус: {linear.status.value}")
    
    # Возможности
    capabilities = linear.get_capabilities()
    print(f"\nВозможности:")
    for cap in capabilities[:5]:
        print(f"  - {cap.name}")
    print()


async def example_4_calendar_integration():
    """
    Пример 4: Работа с Calendar интеграцией
    """
    print("=" * 80)
    print("Пример 4: Calendar Integration")
    print("=" * 80)
    
    calendar = CalendarIntegration()
    
    # Проверка подключения
    status = await calendar.check_health()
    print(f"Статус подключения: {status}")
    
    # Информация
    print(f"\nИнформация об интеграции:")
    print(f"  Название: {calendar.name}")
    print(f"  Сервис: {calendar.service}")
    print(f"  Статус: {calendar.status.value}")
    
    # Возможности
    capabilities = calendar.get_capabilities()
    print(f"\nВозможности:")
    for cap in capabilities[:5]:
        print(f"  - {cap.name}")
    print()


async def example_5_adapters_overview():
    """
    Пример 5: Обзор адаптеров
    """
    print("=" * 80)
    print("Пример 5: REST Adapters Overview")
    print("=" * 80)
    
    adapters_info = [
        ("Microsoft Teams", MicrosoftTeamsAdapter),
        ("Vercel", VercelAdapter),
        ("Calendly", CalendlyAdapter),
    ]
    
    for name, adapter_class in adapters_info:
        print(f"\n{name} Adapter:")
        adapter = adapter_class()
        print(f"  Название: {adapter.name}")
        print(f"  Сервис: {adapter.service}")
        print(f"  Статус: {adapter.status.value}")
        print(f"  Базовый URL: {adapter.base_url}")
        
        # Возможности
        capabilities = adapter.get_capabilities()
        print(f"  Возможности ({len(capabilities)}):")
        for cap in capabilities[:3]:
            print(f"    - {cap.name} ({cap.method} {cap.endpoint})")
        if len(capabilities) > 3:
            print(f"    ... и еще {len(capabilities) - 3}")
    print()


async def example_6_integration_registry():
    """
    Пример 6: Работа с реестром интеграций
    """
    print("=" * 80)
    print("Пример 6: Integration Registry")
    print("=" * 80)
    
    from uaw.integrations.registry import IntegrationRegistry
    
    registry = IntegrationRegistry()
    
    # Получение всех интеграций
    all_integrations = registry.get_all_integrations()
    print(f"Всего интеграций: {len(all_integrations)}")
    
    # Группировка по статусу
    by_status = {}
    for integration in all_integrations:
        status = integration.status.value
        if status not in by_status:
            by_status[status] = []
        by_status[status].append(integration.name)
    
    print(f"\nИнтеграции по статусу:")
    for status, names in by_status.items():
        print(f"  {status}: {len(names)} ({', '.join(names[:3])}{'...' if len(names) > 3 else ''})")
    
    # Получение интеграции по имени
    github = registry.get_integration("github")
    if github:
        print(f"\nGitHub интеграция:")
        print(f"  Статус: {github.status.value}")
        print(f"  Возможности: {len(github.get_capabilities())}")
    print()


async def example_7_capability_mapping():
    """
    Пример 7: Маппинг возможностей
    """
    print("=" * 80)
    print("Пример 7: Capability Mapping")
    print("=" * 80)
    
    # Создание маппинга между действиями и интеграциями
    capability_map = {
        "create_issue": {
            "primary": "github",
            "fallback": ["linear", "asana"],
            "description": "Создание issue/задачи"
        },
        "create_pull_request": {
            "primary": "github",
            "fallback": [],
            "description": "Создание Pull Request"
        },
        "deploy": {
            "primary": "vercel",
            "fallback": ["netlify"],
            "description": "Развертывание"
        },
        "create_event": {
            "primary": "google_calendar",
            "fallback": ["outlook_calendar", "calendly"],
            "description": "Создание события календаря"
        },
        "send_message": {
            "primary": "teams",
            "fallback": ["slack"],
            "description": "Отправка сообщения"
        },
    }
    
    print("Маппинг возможностей:")
    for action, mapping in capability_map.items():
        print(f"\n  {action}:")
        print(f"    Primary: {mapping['primary']}")
        print(f"    Fallback: {', '.join(mapping['fallback']) if mapping['fallback'] else 'None'}")
        print(f"    Description: {mapping['description']}")
    print()


async def example_8_error_handling_in_integrations():
    """
    Пример 8: Обработка ошибок в интеграциях
    """
    print("=" * 80)
    print("Пример 8: Error Handling in Integrations")
    print("=" * 80)
    
    github = GitHubIntegration()
    
    # Пример обработки ошибок
    print("Сценарии обработки ошибок:")
    
    # 1. Недоступная интеграция
    print("\n1. Недоступная интеграция:")
    print("   - Проверяем статус подключения")
    print("   - Используем fallback интеграцию")
    print("   - Уведомляем пользователя")
    
    # 2. Ошибка API
    print("\n2. Ошибка API:")
    print("   - Повторная попытка (retry)")
    print("   - Экспоненциальная задержка")
    print("   - Логирование ошибки")
    
    # 3. Rate limit
    print("\n3. Превышение rate limit:")
    print("   - Ожидание указанного времени")
    print("   - Повторный запрос")
    print("   - Уведомление при частых ошибках")
    
    # 4. Невалидные данные
    print("\n4. Невалидные данные:")
    print("   - Валидация перед отправкой")
    print("   - Возврат ошибки валидации")
    print("   - Запрос уточнения у пользователя")
    print()


async def run_integration_example():
    """Запуск всех примеров интеграций"""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 22 + "UAW INTEGRATION EXAMPLES" + " " * 26 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    
    examples = [
        ("GitHub Integration", example_1_github_integration),
        ("Asana Integration", example_2_asana_integration),
        ("Linear Integration", example_3_linear_integration),
        ("Calendar Integration", example_4_calendar_integration),
        ("Adapters Overview", example_5_adapters_overview),
        ("Integration Registry", example_6_integration_registry),
        ("Capability Mapping", example_7_capability_mapping),
        ("Error Handling", example_8_error_handling_in_integrations),
    ]
    
    for name, example in examples:
        print(f"→ {name}...")
        try:
            await example()
            print(f"✅ {name} выполнен\n")
        except Exception as e:
            print(f"❌ {name} не выполнен: {e}\n")
    
    print("=" * 80)
    print("Все примеры интеграций выполнены!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_integration_example())
