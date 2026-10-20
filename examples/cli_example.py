"""
UAW CLI Example

Command-line interface example for Unified Agentic Workspace.
Demonstrates how to use UAW as a command-line tool.
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any

# Import UAW components
from uaw.core.uaw_core import UAWCore
from uaw.core.state_manager import StateManager
from uaw.core.resource_mapping import ResourceMapper
from uaw.core.security import SecurityManager, PermissionLevel
from uaw.core.audit import AuditLogger, AuditEventType
from uaw.integrations.registry import IntegrationRegistry
from uaw.adapters.registry import AdapterRegistry
from uaw.orchestrator.workflow_engine import WorkflowEngine
from uaw.orchestrator.task_orchestrator import TaskOrchestrator, ExecutionMode
from uaw.scenarios.first_skvoznoy import FirstSkvoznoyScenario
from uaw.models.workflow import Workflow, WorkflowStep, WorkflowStepType, WorkflowStatus
from uaw.models.base import UAWIdentifier


class UAWCLI:
    """Command-line interface for UAW"""

    def __init__(self):
        """Initialize the CLI"""
        self.uaw_core = UAWCore()
        self.state_manager = StateManager()
        self.resource_mapper = ResourceMapper()
        self.security_manager = SecurityManager()
        self.audit_logger = AuditLogger()
        self.integration_registry = IntegrationRegistry()
        self.adapter_registry = AdapterRegistry()
        self.workflow_engine = WorkflowEngine()
        self.task_orchestrator = TaskOrchestrator()
        
        # Initialize components
        self._initialize_components()

    def _initialize_components(self):
        """Initialize all UAW components"""
        # Setup state manager
        self.state_manager.initialize()
        
        # Setup resource mapper
        self.resource_mapper.initialize()
        
        # Setup audit logger
        self.audit_logger.initialize()
        
        # Setup registries
        self.integration_registry.initialize()
        self.adapter_registry.initialize()
        
        # Connect workflow engine components
        self.workflow_engine.state_manager = self.state_manager
        self.workflow_engine.resource_mapper = self.resource_mapper
        self.workflow_engine.security_manager = self.security_manager
        self.workflow_engine.audit_logger = self.audit_logger
        self.workflow_engine.integration_registry = self.integration_registry
        self.workflow_engine.adapter_registry = self.adapter_registry
        
        # Connect task orchestrator
        self.task_orchestrator.state_manager = self.state_manager
        self.task_orchestrator.security_manager = self.security_manager
        self.task_orchestrator.audit_logger = self.audit_logger

    def parse_request(self, request: str) -> Dict[str, Any]:
        """Parse a natural language request"""
        print(f"\n{'='*60}")
        print(f"ПАРСИНГ ЗАПРОСА")
        print(f"{'='*60}")
        print(f"Запрос: {request}")
        
        # Use UAWCore to parse the request
        parsed = self.uaw_core.parse_request(request)
        
        print(f"\nРезультат парсинга:")
        print(f"  Intent: {parsed.get('intent', 'N/A')}")
        print(f"  Action: {parsed.get('action', 'N/A')}")
        print(f"  Entities: {parsed.get('entities', {})}")
        print(f"  Parameters: {parsed.get('parameters', {})}")
        
        return parsed

    def list_integrations(self, service: Optional[str] = None) -> None:
        """List available integrations"""
        print(f"\n{'='*60}")
        print(f"ДОСТУПНЫЕ ИНТЕГРАЦИИ")
        print(f"{'='*60}")
        
        integrations = self.integration_registry.list_integrations()
        adapters = self.adapter_registry.list_adapters()
        
        if service:
            # Filter by service
            print(f"\nИнтеграции для сервиса: {service}")
            for int_name, integration in integrations.items():
                if service.lower() in int_name.lower():
                    self._print_integration_info(int_name, integration)
            
            for adap_name, adapter in adapters.items():
                if service.lower() in adap_name.lower():
                    self._print_adapter_info(adap_name, adapter)
        else:
            # List all
            print(f"\nMCP Интеграции ({len(integrations)}):")
            for int_name, integration in integrations.items():
                self._print_integration_info(int_name, integration)
            
            print(f"\nREST Адаптеры ({len(adapters)}):")
            for adap_name, adapter in adapters.items():
                self._print_adapter_info(adap_name, adapter)

    def _print_integration_info(self, name: str, integration: Any) -> None:
        """Print integration information"""
        status_icon = self._get_status_icon(integration.status)
        print(f"  {status_icon} {name}")
        print(f"      Статус: {integration.status.value}")
        print(f"      Способности: {len(integration.capabilities)} операций")
        print(f"      Авторизация: {integration.auth_type.value if hasattr(integration, 'auth_type') else 'N/A'}")

    def _print_adapter_info(self, name: str, adapter: Any) -> None:
        """Print adapter information"""
        status_icon = self._get_status_icon(adapter.status)
        print(f"  {status_icon} {name}")
        print(f"      Статус: {adapter.status.value}")
        print(f"      Способности: {len(adapter.capabilities)} операций")

    def _get_status_icon(self, status: Any) -> str:
        """Get status icon"""
        if hasattr(status, 'value'):
            status_val = status.value
        else:
            status_val = str(status)
        
        icons = {
            "connected": "✅",
            "available": "✅",
            "partial": "⚠️",
            "read_only": "🔒",
            "unauthorised": "🔐",
            "unavailable": "❌",
        }
        return icons.get(status_val, "⚪")

    def check_integration_status(self, service: str) -> None:
        """Check the status of a specific integration"""
        print(f"\n{'='*60}")
        print(f"СТАТУС ИНТЕГРАЦИИ: {service.upper()}")
        print(f"{'='*60}")
        
        # Check MCP integration
        mcp_integration = self.integration_registry.get_integration(service)
        if mcp_integration:
            print(f"\nMCP Интеграция:")
            print(f"  Статус: {mcp_integration.status.value}")
            print(f"  Авторизация: {mcp_integration.auth_type.value if hasattr(mcp_integration, 'auth_type') else 'N/A'}")
            print(f"  Способности: {len(mcp_integration.capabilities)}")
        else:
            print(f"\nMCP Интеграция: не найдена")
        
        # Check REST adapter
        rest_adapter = self.adapter_registry.get_adapter(service)
        if rest_adapter:
            print(f"\nREST Адаптер:")
            print(f"  Статус: {rest_adapter.status.value}")
            print(f"  Способности: {len(rest_adapter.capabilities)}")
        else:
            print(f"\nREST Адаптер: не найден")

    def run_scenario(self, scenario_name: str, **kwargs) -> None:
        """Run a predefined scenario"""
        print(f"\n{'='*60}")
        print(f"ЗАПУСК СЦЕНАРИЯ: {scenario_name.upper()}")
        print(f"{'='*60}")
        
        scenarios = {
            "first_skvoznoy": FirstSkvoznoyScenario,
            "bug_fix": FirstSkvoznoyScenario,  # Alias
        }
        
        if scenario_name not in scenarios:
            print(f"Сценарий '{scenario_name}' не найден")
            print(f"Доступные сценарии: {', '.join(scenarios.keys())}")
            return
        
        scenario_class = scenarios[scenario_name]
        scenario = scenario_class(
            uaw_core=self.uaw_core,
            state_manager=self.state_manager,
            resource_mapper=self.resource_mapper,
            security_manager=self.security_manager,
            audit_logger=self.audit_logger,
            integration_registry=self.integration_registry,
            adapter_registry=self.adapter_registry
        )
        
        # Run the scenario
        print(f"\nЗапуск сценария...")
        result = asyncio.run(scenario.run(**kwargs))
        
        print(f"\nРезультат:")
        print(f"  Статус: {result.get('status', 'N/A')}")
        print(f"  Сообщение: {result.get('message', 'N/A')}")
        if 'workflow_id' in result:
            print(f"  Workflow ID: {result['workflow_id']}")
        if 'resources' in result:
            print(f"  Созданные ресурсы: {len(result['resources'])}")
            for resource in result['resources']:
                print(f"    - {resource.get('type', 'N/A')}: {resource.get('id', 'N/A')}")

    def create_workflow(self, name: str, steps: List[Dict[str, Any]]) -> None:
        """Create a custom workflow"""
        print(f"\n{'='*60}")
        print(f"СОЗДАНИЕ WORKFLOW: {name.upper()}")
        print(f"{'='*60}")
        
        # Convert steps to WorkflowStep objects
        workflow_steps = []
        for i, step in enumerate(steps):
            workflow_step = WorkflowStep(
                uaw_id=f"step_{i+1}",
                name=step.get('name', f'Step {i+1}'),
                step_type=WorkflowStepType[step.get('type', 'ACTION').upper()],
                description=step.get('description', ''),
                dependencies=step.get('dependencies', []),
                action=step.get('action', ''),
                parameters=step.get('parameters', {})
            )
            workflow_steps.append(workflow_step)
        
        # Create workflow
        workflow = Workflow(
            uaw_id=f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            name=name,
            description="Custom workflow created via CLI",
            steps=workflow_steps,
            status=WorkflowStatus.DRAFT,
            created_at=datetime.utcnow().isoformat()
        )
        
        print(f"\nСоздан workflow:")
        print(f"  ID: {workflow.uaw_id}")
        print(f"  Название: {workflow.name}")
        print(f"  Шагов: {len(workflow.steps)}")
        
        # Save workflow
        workflow_dict = workflow.to_dict()
        workflow_path = f"workflows/{workflow.uaw_id}.json"
        
        # Create workflows directory if it doesn't exist
        import os
        os.makedirs("workflows", exist_ok=True)
        
        with open(workflow_path, 'w') as f:
            json.dump(workflow_dict, f, indent=2, ensure_ascii=False)
        
        print(f"  Сохранён в: {workflow_path}")
        
        # Execute workflow
        print(f"\nЗапуск workflow...")
        result = asyncio.run(self.workflow_engine.execute_workflow(workflow))
        
        print(f"\nРезультат выполнения:")
        print(f"  Статус: {result.status.value}")
        print(f"  Успешных шагов: {result.successful_steps}")
        print(f"  Неуспешных шагов: {result.failed_steps}")

    def execute_workflow(self, workflow_id: str) -> None:
        """Execute an existing workflow"""
        print(f"\n{'='*60}")
        print(f"ВЫПОЛНЕНИЕ WORKFLOW: {workflow_id}")
        print(f"{'='*60}")
        
        # Load workflow
        workflow_path = f"workflows/{workflow_id}.json"
        
        try:
            with open(workflow_path, 'r') as f:
                workflow_dict = json.load(f)
            
            workflow = Workflow.from_dict(workflow_dict)
            
            print(f"\nЗагружен workflow:")
            print(f"  Название: {workflow.name}")
            print(f"  Шагов: {len(workflow.steps)}")
            print(f"  Статус: {workflow.status.value}")
            
            # Execute workflow
            print(f"\nЗапуск workflow...")
            result = asyncio.run(self.workflow_engine.execute_workflow(workflow))
            
            print(f"\nРезультат выполнения:")
            print(f"  Статус: {result.status.value}")
            print(f"  Успешных шагов: {result.successful_steps}")
            print(f"  Неуспешных шагов: {result.failed_steps}")
            
        except FileNotFoundError:
            print(f"Workflow '{workflow_id}' не найден")
        except Exception as e:
            print(f"Ошибка при выполнении workflow: {e}")

    def list_workflows(self) -> None:
        """List all saved workflows"""
        print(f"\n{'='*60}")
        print(f"СПИСОК WORKFLOW")
        print(f"{'='*60}")
        
        import os
        if not os.path.exists("workflows"):
            print("Нет сохранённых workflow")
            return
        
        workflows = []
        for filename in os.listdir("workflows"):
            if filename.endswith(".json"):
                workflow_id = filename.replace(".json", "")
                try:
                    with open(f"workflows/{filename}", 'r') as f:
                        workflow_dict = json.load(f)
                    workflows.append({
                        'id': workflow_id,
                        'name': workflow_dict.get('name', 'N/A'),
                        'status': workflow_dict.get('status', 'N/A'),
                        'steps': len(workflow_dict.get('steps', []))
                    })
                except Exception as e:
                    print(f"Ошибка при загрузке {filename}: {e}")
        
        if not workflows:
            print("Нет сохранённых workflow")
            return
        
        print(f"\nНайдено {len(workflows)} workflow:")
        for wf in workflows:
            print(f"  {wf['id']}")
            print(f"    Название: {wf['name']}")
            print(f"    Статус: {wf['status']}")
            print(f"    Шагов: {wf['steps']}")

    def check_status(self) -> None:
        """Check the status of all UAW components"""
        print(f"\n{'='*60}")
        print(f"СТАТУС UAW КОМПОНЕНТОВ")
        print(f"{'='*60}")
        
        # Check state manager
        print(f"\nState Manager:")
        print(f"  Состояние: {'Инициализирован' if self.state_manager._initialized else 'Не инициализирован'}")
        print(f"  Активных сессий: {len(self.state_manager._states)}")
        
        # Check resource mapper
        print(f"\nResource Mapper:")
        print(f"  Состояние: {'Инициализирован' if self.resource_mapper._initialized else 'Не инициализирован'}")
        print(f"  Сопоставленных ресурсов: {len(self.resource_mapper._resource_map)}")
        
        # Check security manager
        print(f"\nSecurity Manager:")
        print(f"  Уровень по умолчанию: {self.security_manager.default_permission.value}")
        print(f"  Активных сессий: {len(self.security_manager._sessions)}")
        
        # Check registries
        print(f"\nIntegration Registry:")
        integrations = self.integration_registry.list_integrations()
        print(f"  Зарегистрировано интеграций: {len(integrations)}")
        
        print(f"\nAdapter Registry:")
        adapters = self.adapter_registry.list_adapters()
        print(f"  Зарегистрировано адаптеров: {len(adapters)}")

    def interactive_mode(self) -> None:
        """Run in interactive mode"""
        print(f"\n{'='*60}")
        print(f"UAW INTERACTIVE MODE")
        print(f"{'='*60}")
        print(f"\nДоступные команды:")
        print(f"  help, h           - Показать справку")
        print(f"  exit, quit, q     - Выйти")
        print(f"  parse <request>   - Парсинг запроса")
        print(f"  list             - Список интеграций")
        print(f"  check <service>  - Проверить статус интеграции")
        print(f"  run <scenario>   - Запустить сценарий")
        print(f"  create <name>    - Создать workflow")
        print(f"  execute <id>     - Выполнить workflow")
        print(f"  workflows        - Список workflow")
        print(f"  status           - Статус компонентов")
        print(f"\nПример: parse Исправь ошибку в проекте")
        
        while True:
            try:
                command = input(f"\nuaw> ").strip()
                
                if not command:
                    continue
                
                parts = command.split(maxsplit=1)
                cmd = parts[0].lower()
                args = parts[1] if len(parts) > 1 else ""
                
                if cmd in ['exit', 'quit', 'q']:
                    print("Выход...")
                    break
                
                elif cmd in ['help', 'h']:
                    self.interactive_mode()  # Re-show help
                    break
                
                elif cmd == 'parse':
                    if not args:
                        print("Использование: parse <запрос>")
                    else:
                        self.parse_request(args)
                
                elif cmd == 'list':
                    self.list_integrations()
                
                elif cmd == 'check':
                    if not args:
                        print("Использование: check <сервис>")
                    else:
                        self.check_integration_status(args)
                
                elif cmd == 'run':
                    if not args:
                        print("Использование: run <сценарий>")
                    else:
                        self.run_scenario(args)
                
                elif cmd == 'create':
                    print("Введите шаги workflow (по одному на строку, пустая строка для завершения):")
                    steps = []
                    while True:
                        step_line = input("  Шаг: ").strip()
                        if not step_line:
                            break
                        steps.append({'name': step_line})
                    if steps:
                        self.create_workflow(args or f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}", steps)
                    else:
                        print("Нет шагов для создания workflow")
                
                elif cmd == 'execute':
                    if not args:
                        print("Использование: execute <workflow_id>")
                    else:
                        self.execute_workflow(args)
                
                elif cmd == 'workflows':
                    self.list_workflows()
                
                elif cmd == 'status':
                    self.check_status()
                
                else:
                    print(f"Неизвестная команда: {cmd}")
                    print("Введите 'help' для списка команд")
            
            except KeyboardInterrupt:
                print("\nВыход...")
                break
            except Exception as e:
                print(f"Ошибка: {e}")


def main():
    """Main entry point for CLI"""
    parser = argparse.ArgumentParser(
        description='Unified Agentic Workspace - Command Line Interface',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  uaw parse "Исправь ошибку в проекте"
  uaw list
  uaw check github
  uaw run first_skvoznoy
  uaw interactive
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Доступные команды')
    
    # Parse command
    parse_parser = subparsers.add_parser('parse', help='Парсинг запроса')
    parse_parser.add_argument('request', nargs='+', help='Запрос на естественном языке')
    
    # List command
    list_parser = subparsers.add_parser('list', help='Список интеграций')
    list_parser.add_argument('--service', '-s', help='Фильтр по сервису')
    
    # Check command
    check_parser = subparsers.add_parser('check', help='Проверка статуса интеграции')
    check_parser.add_argument('service', help='Название сервиса')
    
    # Run command
    run_parser = subparsers.add_parser('run', help='Запуск сценария')
    run_parser.add_argument('scenario', help='Название сценария')
    run_parser.add_argument('--param', '-p', action='append', nargs=2, 
                           metavar=('KEY', 'VALUE'), help='Параметры сценария')
    
    # Create command
    create_parser = subparsers.add_parser('create', help='Создание workflow')
    create_parser.add_argument('name', help='Название workflow')
    create_parser.add_argument('--steps', '-s', nargs='+', help='Список шагов')
    
    # Execute command
    execute_parser = subparsers.add_parser('execute', help='Выполнение workflow')
    execute_parser.add_argument('workflow_id', help='ID workflow')
    
    # List workflows command
    workflows_parser = subparsers.add_parser('workflows', help='Список workflow')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Статус компонентов')
    
    # Interactive mode
    interactive_parser = subparsers.add_parser('interactive', help='Интерактивный режим')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize CLI
    cli = UAWCLI()
    
    # Execute command
    if args.command == 'parse':
        request = ' '.join(args.request)
        cli.parse_request(request)
    
    elif args.command == 'list':
        cli.list_integrations(args.service)
    
    elif args.command == 'check':
        cli.check_integration_status(args.service)
    
    elif args.command == 'run':
        params = dict(args.param) if args.param else {}
        cli.run_scenario(args.scenario, **params)
    
    elif args.command == 'create':
        steps = []
        if args.steps:
            for step in args.steps:
                steps.append({'name': step})
        cli.create_workflow(args.name, steps)
    
    elif args.command == 'execute':
        cli.execute_workflow(args.workflow_id)
    
    elif args.command == 'workflows':
        cli.list_workflows()
    
    elif args.command == 'status':
        cli.check_status()
    
    elif args.command == 'interactive':
        cli.interactive_mode()
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
