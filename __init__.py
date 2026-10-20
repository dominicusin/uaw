"""
Unified Agentic Workspace (UAW)
Единая интеллектуальная агентная система для оркестрации рабочих процессов
через множественные интеграции (GitHub, Asana, Calendar, и др.)
"""

__version__ = "0.1.0"
__author__ = "Vibe Code Agent"
__description__ = "Unified Agentic Workspace - Единая агентная система"

# Инициализация модулей
from .core import UAWCore
from .models import (
    Person, Team, Project, Task, Issue, Repository,
    Deployment, Document, Event, Workflow, Integration,
    Approval, AuditEvent, ResourceMapping
)
from .integrations import IntegrationRegistry
from .orchestrator import TaskOrchestrator
from .adapters import AdapterRegistry

__all__ = [
    "UAWCore",
    "Person", "Team", "Project", "Task", "Issue", "Repository",
    "Deployment", "Document", "Event", "Workflow", "Integration",
    "Approval", "AuditEvent", "ResourceMapping",
    "IntegrationRegistry", "TaskOrchestrator", "AdapterRegistry"
]
