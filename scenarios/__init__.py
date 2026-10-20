"""
UAW Scenarios Module
Сценарии автоматизации для Unified Agentic Workspace
"""

from .first_skvoznoy import (
    FirstSkvoznoyScenario,
    FixBugWorkflow,
    execute_fix_bug_scenario,
    FIX_BUG_WORKFLOW_DEFINITION,
)

__all__ = [
    "FirstSkvoznoyScenario",
    "FixBugWorkflow",
    "execute_fix_bug_scenario",
    "FIX_BUG_WORKFLOW_DEFINITION",
]
