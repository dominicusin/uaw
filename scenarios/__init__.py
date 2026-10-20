"""
UAW Scenarios Module
Сценарии автоматизации для Unified Agentic Workspace
"""

from .first_skvoznoy import (
    FirstSkvoznoyScenario,
    FixBugWorkflow,
    execute_fix_bug_scenario,
    FIX_BUG_WORKFLOW_DEFINITION,
    ScenarioReport,
    StepResult,
    StepResultStatus,
)

from .create_task_scenario import (
    CreateTaskWorkflow,
    create_task,
    CREATE_TASK_WORKFLOW_DEFINITION,
    CreateTaskResult,
)

from .deploy_scenario import (
    DeployWorkflow,
    deploy,
    DEPLOY_WORKFLOW_DEFINITION,
    DeployResult,
)

from .notification_scenario import (
    NotificationWorkflow,
    send_notification,
    NOTIFICATION_WORKFLOW_DEFINITION,
    NotificationResult,
    NotificationType,
    notify_task_completed,
    notify_task_assigned,
    notify_deployment_completed,
    notify_deployment_failed,
    notify_pr_created,
    notify_pr_merged,
)

__all__ = [
    # First Skvoznoy
    "FirstSkvoznoyScenario",
    "FixBugWorkflow",
    "execute_fix_bug_scenario",
    "FIX_BUG_WORKFLOW_DEFINITION",
    "ScenarioReport",
    "StepResult",
    "StepResultStatus",
    
    # Create Task
    "CreateTaskWorkflow",
    "create_task",
    "CREATE_TASK_WORKFLOW_DEFINITION",
    "CreateTaskResult",
    
    # Deploy
    "DeployWorkflow",
    "deploy",
    "DEPLOY_WORKFLOW_DEFINITION",
    "DeployResult",
    
    # Notification
    "NotificationWorkflow",
    "send_notification",
    "NOTIFICATION_WORKFLOW_DEFINITION",
    "NotificationResult",
    "NotificationType",
    "notify_task_completed",
    "notify_task_assigned",
    "notify_deployment_completed",
    "notify_deployment_failed",
    "notify_pr_created",
    "notify_pr_merged",
]
