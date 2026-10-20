"""
UAW Advanced Workflow Examples
Примеры сложных workflow для Unified Agentic Workspace
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from uaw.core.uaw_core import UAWCore
from uaw.core.state_manager import StateManager
from uaw.core.resource_mapping import ResourceMapper
from uaw.core.security import SecurityManager, PermissionLevel
from uaw.core.audit import AuditLogger

from uaw.models.workflow import Workflow, WorkflowStep, WorkflowStepType, WorkflowStatus
from uaw.models.issue import Issue, IssueType, IssueSeverity, IssueStatus
from uaw.models.task import Task, TaskStatus, TaskPriority
from uaw.models.repository import Repository, Branch, PullRequest, PullRequestStatus
from uaw.models.deployment import Deployment, DeploymentStatus
from uaw.models.person import Person

from uaw.scenarios import (
    execute_fix_bug_scenario,
    create_task,
    deploy,
    send_notification,
    NotificationType,
)


async def example_1_fix_bug_workflow():
    """
    Пример 1: Полный workflow исправления бага
    """
    print("=" * 80)
    print("Пример 1: Полный workflow исправления бага")
    print("=" * 80)
    
    # Запуск сквозного сценария
    report = await execute_fix_bug_scenario(
        project_name="my-web-app",
        bug_title="Fix critical login bug",
        bug_description="""
        Users cannot login when password contains special characters.
        
        Steps to reproduce:
        1. Go to login page
        2. Enter username: test@example.com
        3. Enter password: P@ssw0rd!
        4. Click login
        5. Error: Invalid credentials
        
        Expected: User should be logged in
        Actual: Authentication fails
        """,
        assignee={
            "name": "John Doe",
            "github": "johndoe",
            "asana": "john@company",
            "linear": "john",
            "email": "john@company.com",
            "teams_id": "user123",
        },
        severity="critical",
        priority="urgent",
        labels=["bug", "authentication", "critical", "security"],
    )
    
    print(f"Сценарий выполнен: {report.status.value}")
    print(f"Время выполнения: {report.execution_time_seconds:.2f} секунд")
    print(f"Всего этапов: {len(report.steps)}")
    print(f"Выполнено: {len(report.get_completed_steps())}")
    print(f"Ошибки: {len(report.get_failed_steps())}")
    print(f"Заблокировано: {len(report.get_blocked_steps())}")
    print()
    
    # Вывод отчёта
    print("Отчёт:")
    print("-" * 40)
    print(report.to_markdown())
    print()


async def example_2_create_task_workflow():
    """
    Пример 2: Создание задачи в Asana/Linear
    """
    print("=" * 80)
    print("Пример 2: Создание задачи")
    print("=" * 80)
    
    # Создание задачи
    result = await create_task(
        title="Implement new authentication system",
        project_name="MyApp",
        assignee_name="John Doe",
        description="""
        Implement OAuth2 authentication with support for:
        - Google
        - GitHub
        - Microsoft
        
        Requirements:
        - Secure token storage
        - Token refresh
        - User profile management
        """,
        priority="high",
        due_date="2025-12-31",
        tags=["authentication", "feature", "high-priority"],
        workspace="default",
    )
    
    print(f"Задача создана: {result.task_id}")
    print(f"Заголовок: {result.title}")
    print(f"Проект: {result.project_id}")
    print(f"Исполнитель: {result.assignee_id}")
    print(f"Приоритет: {result.priority}")
    print(f"Срок: {result.due_date}")
    print(f"URL: {result.task_url}")
    print()


async def example_3_deploy_workflow():
    """
    Пример 3: Развертывание приложения
    """
    print("=" * 80)
    print("Пример 3: Развертывание приложения")
    print("=" * 80)
    
    # Развертывание
    result = await deploy(
        repository_id="repo:my-web-app",
        branch="main",
        environment="production",
        comment="Deployment v1.2.0 from UAW",
    )
    
    print(f"Deployment создан: {result.deployment_id}")
    print(f"URL: {result.deployment_url}")
    print(f"Статус: {result.status}")
    print(f"Окружение: {result.environment}")
    print(f"Ветка: {result.branch}")
    print(f"Коммит: {result.commit_sha}")
    print()


async def example_4_notification_workflow():
    """
    Пример 4: Отправка уведомлений
    """
    print("=" * 80)
    print("Пример 4: Отправка уведомлений")
    print("=" * 80)
    
    # Уведомление о завершении задачи
    result1 = await send_notification(
        message="Задача 'Implement authentication' успешно завершена!",
        channel="general",
        notification_type=NotificationType.TASK_COMPLETED,
        title="Задача завершена",
        team="Dev Team",
    )
    
    print(f"Уведомление 1 отправлено: {result1.delivered}")
    print(f"  ID: {result1.notification_id}")
    print(f"  Тип: {result1.notification_type.value}")
    print()
    
    # Уведомление о развертывании
    result2 = await send_notification(
        message="Развертывание v1.2.0 в production завершено успешно!",
        channel="deployments",
        notification_type=NotificationType.DEPLOYMENT_COMPLETED,
        title="Развертывание завершено",
        team="DevOps Team",
    )
    
    print(f"Уведомление 2 отправлено: {result2.delivered}")
    print(f"  ID: {result2.notification_id}")
    print(f"  Тип: {result2.notification_type.value}")
    print()


async def example_5_complex_workflow():
    """
    Пример 5: Комплексный workflow с несколькими сценариями
    """
    print("=" * 80)
    print("Пример 5: Комплексный workflow")
    print("=" * 80)
    
    core = UAWCore()
    
    # Создание комплексного запроса
    complex_request = """
    Исправь критичный баг в проекте MyApp:
    1. Создай issue в GitHub с меткой 'critical'
    2. Создай связанную задачу в Asana
    3. Назначь на John Doe
    4. Создай ветку для исправления
    5. После исправления разверни на staging
    6. Уведоми команду в Teams
    """
    
    print(f"Запрос: {complex_request}")
    print()
    
    # Парсинг запроса
    parsed = core.parse_request(complex_request)
    print(f"Распарсенный intent: {parsed.get('intent')}")
    print(f"Действия: {parsed.get('actions')}")
    print()
    
    # Планирование workflow
    workflow = core.plan_workflow(complex_request)
    print(f"Спланирован workflow: {workflow.name}")
    print(f"Количество этапов: {len(workflow.steps)}")
    print()
    
    # Показать этапы
    print("Этапы workflow:")
    for i, step in enumerate(workflow.steps, 1):
        print(f"  {i}. {step.name}")
        if step.dependencies:
            print(f"     Зависимости: {step.dependencies}")
    print()


async def example_6_parallel_workflows():
    """
    Пример 6: Параллельное выполнение workflow
    """
    print("=" * 80)
    print("Пример 6: Параллельное выполнение")
    print("=" * 80)
    
    core = UAWCore()
    
    # Создание нескольких workflow
    workflows = []
    
    # Workflow 1: Создание задачи
    workflow1 = core.plan_workflow("Создай задачу Test 1 в проекте MyApp")
    workflows.append(("Task 1", workflow1))
    
    # Workflow 2: Создание задачи
    workflow2 = core.plan_workflow("Создай задачу Test 2 в проекте MyApp")
    workflows.append(("Task 2", workflow2))
    
    # Workflow 3: Создание задачи
    workflow3 = core.plan_workflow("Создай задачу Test 3 в проекте MyApp")
    workflows.append(("Task 3", workflow3))
    
    print(f"Создано workflow: {len(workflows)}")
    
    # В реальности здесь было бы параллельное выполнение
    # Для примера просто показываем информацию
    for name, workflow in workflows:
        print(f"\n{name}:")
        print(f"  ID: {workflow.uaw_id}")
        print(f"  Этапов: {len(workflow.steps)}")
    print()


async def example_7_workflow_with_conditions():
    """
    Пример 7: Workflow с условиями
    """
    print("=" * 80)
    print("Пример 7: Workflow с условиями")
    print("=" * 80)
    
    # Создание workflow с условиями
    workflow = Workflow(
        uaw_id="conditional-workflow-1",
        name="Workflow с условиями",
        description="Workflow с проверкой условий",
        status=WorkflowStatus.PENDING,
        steps=[
            WorkflowStep(
                uaw_id="step-1",
                name="Проверка условий",
                step_type=WorkflowStepType.CONDITION,
                description="Проверка, что все параметры валидны",
                action="validate",
                parameters={"required_fields": ["title", "assignee"]},
                dependencies=[],
                timeout_seconds=30,
                retry_count=0,
                permission_level=PermissionLevel.L0_READ_ONLY,
            ),
            WorkflowStep(
                uaw_id="step-2",
                name="Создание ресурса",
                step_type=WorkflowStepType.ACTION,
                description="Создание ресурса при условии успешной проверки",
                action="create_resource",
                parameters={},
                dependencies=["step-1"],
                timeout_seconds=60,
                retry_count=2,
                permission_level=PermissionLevel.L2_SUPERVISED,
            ),
            WorkflowStep(
                uaw_id="step-3",
                name="Уведомление об успехе",
                step_type=WorkflowStepType.ACTION,
                description="Уведомление при успешном создании",
                action="notify",
                parameters={},
                dependencies=["step-2"],
                timeout_seconds=30,
                retry_count=1,
                permission_level=PermissionLevel.L2_SUPERVISED,
            ),
        ],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    
    print(f"Создан workflow с условиями: {workflow.name}")
    print(f"Этапы:")
    for step in workflow.steps:
        print(f"  - {step.name} ({step.step_type.value})")
        if step.dependencies:
            print(f"    Зависимости: {step.dependencies}")
    print()


async def example_8_error_handling():
    """
    Пример 8: Обработка ошибок
    """
    print("=" * 80)
    print("Пример 8: Обработка ошибок")
    print("=" * 80)
    
    # Создание workflow с обработкой ошибок
    workflow = Workflow(
        uaw_id="error-handling-workflow-1",
        name="Workflow с обработкой ошибок",
        description="Демонстрация обработки ошибок",
        status=WorkflowStatus.PENDING,
        steps=[
            WorkflowStep(
                uaw_id="step-1",
                name="Этап с высоким риском",
                step_type=WorkflowStepType.ACTION,
                description="Этап, который может завершиться ошибкой",
                action="risky_operation",
                parameters={},
                dependencies=[],
                timeout_seconds=60,
                retry_count=3,
                retry_delay=10,
                permission_level=PermissionLevel.L2_SUPERVISED,
            ),
            WorkflowStep(
                uaw_id="step-2",
                name="Резервный этап",
                step_type=WorkflowStepType.ACTION,
                description="Выполняется, если первый этап провален",
                action="fallback_operation",
                parameters={},
                dependencies=["step-1"],
                timeout_seconds=30,
                retry_count=1,
                permission_level=PermissionLevel.L2_SUPERVISED,
            ),
            WorkflowStep(
                uaw_id="step-3",
                name="Уведомление об ошибке",
                step_type=WorkflowStepType.ACTION,
                description="Уведомление при ошибке",
                action="notify_error",
                parameters={},
                dependencies=["step-1"],
                timeout_seconds=30,
                retry_count=0,
                permission_level=PermissionLevel.L2_SUPERVISED,
            ),
        ],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    
    print(f"Создан workflow с обработкой ошибок: {workflow.name}")
    print(f"Этапы:")
    for step in workflow.steps:
        print(f"  - {step.name}")
        print(f"    Retry count: {step.retry_count}")
        print(f"    Retry delay: {step.retry_delay}")
    print()


async def run_advanced_example():
    """Запуск всех расширенных примеров"""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "UAW ADVANCED WORKFLOW EXAMPLES" + " " * 24 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    
    examples = [
        ("Сценарий исправления бага", example_1_fix_bug_workflow),
        ("Создание задачи", example_2_create_task_workflow),
        ("Развертывание", example_3_deploy_workflow),
        ("Отправка уведомлений", example_4_notification_workflow),
        ("Комплексный workflow", example_5_complex_workflow),
        ("Параллельное выполнение", example_6_parallel_workflows),
        ("Workflow с условиями", example_7_workflow_with_conditions),
        ("Обработка ошибок", example_8_error_handling),
    ]
    
    for name, example in examples:
        print(f"→ {name}...")
        try:
            await example()
            print(f"✅ {name} выполнен\n")
        except Exception as e:
            print(f"❌ {name} не выполнен: {e}\n")
    
    print("=" * 80)
    print("Все расширенные примеры выполнены!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_advanced_example())
