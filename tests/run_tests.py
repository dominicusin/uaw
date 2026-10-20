"""
UAW Test Runner
Запуск всех тестов для Unified Agentic Workspace
"""

import unittest
import sys
import os
from datetime import datetime

# Добавляем корневой каталог в path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Импортируем все тесты
from uaw.tests.test_core import (
    TestUAWCore,
    TestStateManager,
    TestResourceMapper,
    TestSecurityManager,
    TestAuditLogger,
)
from uaw.tests.test_models import (
    TestBaseModels,
    TestPerson,
    TestTeam,
    TestProject,
    TestTask,
    TestIssue,
    TestRepository,
    TestDeployment,
    TestDocument,
    TestEvent,
    TestWorkflow,
    TestIntegration,
    TestApproval,
    TestAuditEvent,
)
from uaw.tests.test_scenarios import (
    TestFixBugWorkflow,
    TestFirstSkvoznoyScenario,
    TestExecuteFixBugScenario,
    TestScenarioReport,
    TestStepResult,
)


def create_test_suite():
    """Создание тестового suite"""
    suite = unittest.TestSuite()
    
    # Core tests
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestUAWCore))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestStateManager))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestResourceMapper))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestSecurityManager))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestAuditLogger))
    
    # Model tests
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestBaseModels))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestPerson))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestTeam))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestProject))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestTask))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestIssue))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestRepository))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestDeployment))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestDocument))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestEvent))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestWorkflow))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestIntegration))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestApproval))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestAuditEvent))
    
    # Scenario tests
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestFixBugWorkflow))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestFirstSkvoznoyScenario))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestExecuteFixBugScenario))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestScenarioReport))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestStepResult))
    
    return suite


def run_all_tests(verbosity: int = 2) -> bool:
    """
    Запуск всех тестов
    
    Args:
        verbosity: Уровень детализации вывода (0-2)
        
    Returns:
        bool: True если все тесты прошли успешно
    """
    print("=" * 80)
    print("UAW Test Suite - Unified Agentic Workspace")
    print("=" * 80)
    print(f"Start time: {datetime.utcnow()}")
    print()
    
    suite = create_test_suite()
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)
    
    print()
    print("=" * 80)
    print("Test Summary")
    print("=" * 80)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    print(f"Success rate: {(result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100:.1f}%")
    print(f"End time: {datetime.utcnow()}")
    print("=" * 80)
    
    return result.wasSuccessful()


def run_tests_by_category(category: str, verbosity: int = 2) -> bool:
    """
    Запуск тестов по категории
    
    Args:
        category: Категория тестов (core, models, scenarios, all)
        verbosity: Уровень детализации вывода
        
    Returns:
        bool: True если все тесты прошли успешно
    """
    suite = unittest.TestSuite()
    
    if category == "all":
        suite = create_test_suite()
    elif category == "core":
        suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestUAWCore))
        suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestStateManager))
        suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestResourceMapper))
        suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestSecurityManager))
        suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestAuditLogger))
    elif category == "models":
        suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestBaseModels))
        suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestPerson))
        suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestTeam))
        suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestProject))
        suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestTask))
        suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestIssue))
        suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestRepository))
        suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestDeployment))
        suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestDocument))
        suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestEvent))
        suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestWorkflow))
        suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestIntegration))
        suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestApproval))
        suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestAuditEvent))
    elif category == "scenarios":
        suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestFixBugWorkflow))
        suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestFirstSkvoznoyScenario))
        suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestExecuteFixBugScenario))
        suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestScenarioReport))
        suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestStepResult))
    else:
        print(f"Unknown category: {category}")
        print("Available categories: core, models, scenarios, all")
        return False
    
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    # Проверка аргументов командной строки
    category = sys.argv[1] if len(sys.argv) > 1 else "all"
    verbosity = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    
    if category == "all":
        success = run_all_tests(verbosity)
    else:
        success = run_tests_by_category(category, verbosity)
    
    # Выход с кодом 0 если все тесты прошли
    sys.exit(0 if success else 1)
