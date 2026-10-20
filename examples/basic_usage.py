"""
UAW Basic Usage Examples
Основные примеры использования Unified Agentic Workspace
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional

# Импорт компонентов UAW
from uaw.core.uaw_core import UAWCore
from uaw.core.state_manager import StateManager
from uaw.core.resource_mapping import ResourceMapper
from uaw.core.security import SecurityManager, PermissionLevel
from uaw.core.audit import AuditLogger

from uaw.models.workflow import Workflow, WorkflowStep, WorkflowStepType, WorkflowStatus
from uaw.models.person import Person
from uaw.models.task import Task, TaskStatus, TaskPriority
from uaw.models.issue import Issue, IssueType, IssueSeverity


def example_1_simple_request():
    """
    Пример 1: Простой запрос на естественном языке
    """
    print("=" * 80)
    print("Пример 1: Простой запрос на естественном языке")
    print("=" * 80)
    
    # Создание экземпляра UAW Core
    core = UAWCore()
    
    # Запрос на естественном языке
    request = "Создай задачу для проекта MyApp"
    
    # Парсинг запроса
    parsed = core.parse_request(request)
    print(f"Запрос: {request}")
    print(f"Распарсенный intent: {parsed.get('intent')}")
    print(f"Сущности: {parsed.get('entities')}")
    print(f"Действия: {parsed.get('actions')}")
    print()


def example_2_create_workflow():
    """
    Пример 2: Создание workflow вручную
    """
    print("=" * 80)
    print("Пример 2: Создание workflow вручную")
    print("=" * 80)
    
    # Создание workflow с этапами
    workflow = Workflow(
        uaw_id="example-workflow-1",
        name="Пример workflow",
        description="Простой workflow для демонстрации",
        status=WorkflowStatus.PENDING,
        steps=[
            WorkflowStep(
                uaw_id="step-1",
                name="Этап 1: Создание задачи",
                step_type=WorkflowStepType.ACTION,
                description="Создание задачи в системе",
                integration="asana",
                action="create_task",
                parameters={
                    "title": "Тестовая задача",
                    "description": "Описание тестовой задачи",
                    "priority": "high"
                },
                dependencies=[],
                timeout_seconds=60,
                retry_count=2,
                permission_level=PermissionLevel.L2_SUPERVISED,
            ),
            WorkflowStep(
                uaw_id="step-2",
                name="Этап 2: Уведомление",
                step_type=WorkflowStepType.ACTION,
                description="Уведомление о создании задачи",
                adapter="teams",
                action="send_message",
                parameters={
                    "message": "Задача создана успешно!"
                },
                dependencies=["step-1"],
                timeout_seconds=30,
                retry_count=1,
                permission_level=PermissionLevel.L2_SUPERVISED,
            ),
        ],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    
    print(f"Создан workflow: {workflow.name}")
    print(f"ID: {workflow.uaw_id}")
    print(f"Количество этапов: {len(workflow.steps)}")
    print(f"Статус: {workflow.status.value}")
    
    for step in workflow.steps:
        print(f"  - {step.name} ({step.uaw_id})")
    print()


def example_3_work_with_models():
    """
    Пример 3: Работа с моделями данных
    """
    print("=" * 80)
    print("Пример 3: Работа с моделями данных")
    print("=" * 80)
    
    # Создание Person
    person = Person(
        uaw_id="person:john-doe",
        name="John Doe",
        email="john@example.com",
        external_ids={
            "github": "johndoe",
            "asana": "user-123",
            "linear": "user-456"
        },
        teams=["team:dev-team"],
        roles=["developer", "team-lead"],
        timezone="UTC",
    )
    
    print(f"Создан Person: {person.name}")
    print(f"  ID: {person.uaw_id}")
    print(f"  Email: {person.email}")
    print(f"  GitHub: {person.external_ids.get('github')}")
    print(f"  Команды: {person.teams}")
    print(f"  Роли: {person.roles}")
    print()
    
    # Создание Task
    task = Task(
        uaw_id="task:fix-login",
        title="Исправить ошибку авторизации",
        description="Пользователи не могут войти в систему",
        status=TaskStatus.TODO,
        priority=TaskPriority.HIGH,
        assignee_id="person:john-doe",
        project_id="project:myapp",
        due_date=datetime(2025, 12, 31),
    )
    
    print(f"Создана Task: {task.title}")
    print(f"  ID: {task.uaw_id}")
    print(f"  Статус: {task.status.value}")
    print(f"  Приоритет: {task.priority.value}")
    print(f"  Исполнитель: {task.assignee_id}")
    print(f"  Срок: {task.due_date}")
    print()
    
    # Создание Issue
    issue = Issue(
        uaw_id="issue:login-bug",
        title="Login bug in production",
        description="Critical login issue affecting all users",
        issue_type=IssueType.BUG,
        severity=IssueSeverity.CRITICAL,
        status=IssueStatus.OPEN,
        repository_id="repo:myapp",
        assignee_id="person:john-doe",
        labels=["bug", "authentication", "critical"],
    )
    
    print(f"Создана Issue: {issue.title}")
    print(f"  ID: {issue.uaw_id}")
    print(f"  Тип: {issue.issue_type.value}")
    print(f"  Уровень: {issue.severity.value}")
    print(f"  Метки: {issue.labels}")
    print()


def example_4_resource_mapping():
    """
    Пример 4: Сопоставление ресурсов между сервисами
    """
    print("=" * 80)
    print("Пример 4: Сопоставление ресурсов")
    print("=" * 80)
    
    # Создание ResourceMapper
    mapper = ResourceMapper()
    
    # Генерация UAW ID
    uaw_id = mapper.generate_uaw_id("issue", "github")
    print(f"Сгенерирован UAW ID: {uaw_id}")
    
    # Связывание ресурсов
    external_ids = {
        "github": "issue-123",
        "asana": "task-456",
        "linear": "issue-789"
    }
    
    for service, external_id in external_ids.items():
        mapper.link_resources(uaw_id, external_id, service)
        print(f"Связан {service}: {external_id} -> {uaw_id}")
    
    # Получение внешних ID
    print(f"\nВнешние ID для {uaw_id}:")
    for service in ["github", "asana", "linear"]:
        ext_id = mapper.get_external_id(uaw_id, service)
        print(f"  {service}: {ext_id}")
    
    # Обратное сопоставление
    print(f"\nUAW ID для github:issue-123: {mapper.get_uaw_id('issue-123', 'github')}")
    print()


def example_5_security_checks():
    """
    Пример 5: Проверка безопасности
    """
    print("=" * 80)
    print("Пример 5: Проверка безопасности")
    print("=" * 80)
    
    security = SecurityManager()
    
    # Проверка уровней доступа
    levels = [
        PermissionLevel.L0_READ_ONLY,
        PermissionLevel.L1_PREPARE,
        PermissionLevel.L2_SUPERVISED,
        PermissionLevel.L3_POLICY_BASED,
        PermissionLevel.L4_RESTRICTED,
    ]
    
    print("Уровни автономности:")
    for level in levels:
        print(f"  {level.value}: {level.name}")
    
    # Генерация токена
    token = security.generate_session_token("user-123")
    print(f"\nСгенерирован токен: {token[:20]}...")
    
    # Проверка токена
    is_valid = security.validate_session_token(token)
    print(f"Токен валиден: {is_valid}")
    
    # Проверка разрешений
    permissions = [
        ("list_repositories", "github", "L0_READ_ONLY"),
        ("create_task", "asana", "L2_SUPERVISED"),
        ("delete_production", "github", "L4_RESTRICTED"),
    ]
    
    print("\nПроверка разрешений:")
    for action, integration, expected_level in permissions:
        # В реальности это асинхронный метод
        # Для примера просто показываем ожидаемый результат
        if expected_level == "L4_RESTRICTED":
            result = False  # L4 требует явного подтверждения
        else:
            result = True
        print(f"  {action} ({integration}): {'✅ Разрешено' if result else '❌ Запрещено'}")
    print()


def example_6_audit_logging():
    """
    Пример 6: Аудит и логирование
    """
    print("=" * 80)
    print("Пример 6: Аудит и логирование")
    print("=" * 80)
    
    audit = AuditLogger()
    
    # Создание события аудита
    import asyncio
    
    async def log_events():
        # Логирование события
        event = audit.create_event(
            event_type="workflow_started",
            resource_type="workflow",
            resource_id="workflow-123",
            action="execute",
            status="started",
            details={"user": "admin", "workflow": "fix-bug"},
        )
        await audit.log_event(event)
        print("Событие залоггировано:")
        print(f"  Тип: {event.event_type}")
        print(f"  Ресурс: {event.resource_type}:{event.resource_id}")
        print(f"  Действие: {event.action}")
        print(f"  Статус: {event.status}")
        print(f"  Детали: {event.details}")
        
        # Получение событий
        events = audit.get_events(resource_type="workflow")
        print(f"\nВсего событий в логе: {len(events)}")
    
    asyncio.run(log_events())
    print()


def example_7_state_management():
    """
    Пример 7: Управление состоянием
    """
    print("=" * 80)
    print("Пример 7: Управление состоянием")
    print("=" * 80)
    
    state_manager = StateManager()
    
    # Создание состояния workflow
    from uaw.core.state_manager import WorkflowState
    
    workflow_state = WorkflowState(
        workflow_id="workflow-123",
        current_step="step-2",
        completed_steps=["step-1"],
        pending_steps=["step-2", "step-3"],
        failed_steps=[],
        context={
            "user_id": "user-123",
            "project": "my-project",
            "created_resources": {
                "task_id": "task-456",
                "issue_id": "issue-789"
            }
        },
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    
    # Сохранение состояния
    state_manager.save_state("workflow-123", workflow_state)
    print("Состояние сохранено:")
    print(f"  Workflow ID: {workflow_state.workflow_id}")
    print(f"  Текущий этап: {workflow_state.current_step}")
    print(f"  Завершенные этапы: {workflow_state.completed_steps}")
    
    # Получение состояния
    retrieved_state = state_manager.get_state("workflow-123")
    print(f"\nСостояние извлечено: {retrieved_state is not None}")
    
    # Список всех состояний
    all_states = state_manager.list_states()
    print(f"Всего сохраненных состояний: {len(all_states)}")
    
    # Удаление состояния
    state_manager.delete_state("workflow-123")
    deleted_state = state_manager.get_state("workflow-123")
    print(f"Состояние удалено: {deleted_state is None}")
    print()


def run_basic_example():
    """Запуск всех основных примеров"""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "UAW BASIC USAGE EXAMPLES" + " " * 28 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    
    examples = [
        example_1_simple_request,
        example_2_create_workflow,
        example_3_work_with_models,
        example_4_resource_mapping,
        example_5_security_checks,
        example_6_audit_logging,
        example_7_state_management,
    ]
    
    for i, example in enumerate(examples, 1):
        try:
            example()
        except Exception as e:
            print(f"Ошибка в примере {i}: {e}")
            print()
    
    print("=" * 80)
    print("Все основные примеры выполнены!")
    print("=" * 80)


if __name__ == "__main__":
    run_basic_example()
