"""
UAW API Example

REST API example for Unified Agentic Workspace.
Demonstrates how to expose UAW functionality as a REST API using FastAPI.
"""

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum
import uuid
import asyncio
import json
import os

# Import UAW components
from uaw.core.uaw_core import UAWCore
from uaw.core.state_manager import StateManager
from uaw.core.resource_mapping import ResourceMapper
from uaw.core.security import SecurityManager, PermissionLevel
from uaw.core.audit import AuditLogger, AuditEventType
from uaw.integrations.registry import IntegrationRegistry
from uaw.adapters.registry import AdapterRegistry
from uaw.orchestrator.workflow_engine import WorkflowEngine, WorkflowExecutionResult
from uaw.orchestrator.task_orchestrator import TaskOrchestrator, ExecutionMode
from uaw.scenarios.first_skvoznoy import FirstSkvoznoyScenario
from uaw.models.workflow import Workflow, WorkflowStep, WorkflowStepType, WorkflowStatus
from uaw.models.base import UAWIdentifier
from uaw.models.person import Person
from uaw.models.project import Project
from uaw.models.task import Task, TaskPriority, TaskStatus
from uaw.models.issue import Issue, IssuePriority, IssueStatus


# Initialize FastAPI app
app = FastAPI(
    title="Unified Agentic Workspace API",
    description="REST API for UAW - Unified Agentic Workspace",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Initialize UAW components
uaw_core = UAWCore()
state_manager = StateManager()
resource_mapper = ResourceMapper()
security_manager = SecurityManager()
audit_logger = AuditLogger()
integration_registry = IntegrationRegistry()
adapter_registry = AdapterRegistry()
workflow_engine = WorkflowEngine()
task_orchestrator = TaskOrchestrator()

# Connect components
state_manager.initialize()
resource_mapper.initialize()
audit_logger.initialize()
integration_registry.initialize()
adapter_registry.initialize()

workflow_engine.state_manager = state_manager
workflow_engine.resource_mapper = resource_mapper
workflow_engine.security_manager = security_manager
workflow_engine.audit_logger = audit_logger
workflow_engine.integration_registry = integration_registry
workflow_engine.adapter_registry = adapter_registry

task_orchestrator.state_manager = state_manager
task_orchestrator.security_manager = security_manager
task_orchestrator.audit_logger = audit_logger

# Store workflows in memory (in production, use a database)
workflows_store: Dict[str, Workflow] = {}
execution_results: Dict[str, WorkflowExecutionResult] = {}


# Models
class HealthResponse(BaseModel):
    """Health check response"""
    status: str = "healthy"
    version: str = "1.0.0"
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    components: Dict[str, str] = {}


class ParseRequest(BaseModel):
    """Request model for parsing natural language"""
    request: str = Field(..., description="Natural language request")
    session_id: Optional[str] = Field(None, description="Session ID for tracking")
    user_id: Optional[str] = Field(None, description="User ID for authorization")


class ParseResponse(BaseModel):
    """Response model for parsed request"""
    intent: str
    action: str
    entities: Dict[str, Any] = {}
    parameters: Dict[str, Any] = {}
    confidence: float = 0.0
    workflow_plan: Optional[List[Dict[str, Any]]] = None


class WorkflowCreateRequest(BaseModel):
    """Request model for creating a workflow"""
    name: str = Field(..., description="Workflow name")
    description: Optional[str] = Field(None, description="Workflow description")
    steps: List[Dict[str, Any]] = Field(..., description="List of workflow steps")
    dependencies: Optional[Dict[str, List[str]]] = Field(None, description="Step dependencies")


class WorkflowResponse(BaseModel):
    """Response model for workflow"""
    id: str
    name: str
    description: Optional[str] = None
    status: str
    steps: List[Dict[str, Any]]
    created_at: str
    updated_at: Optional[str] = None


class WorkflowExecutionRequest(BaseModel):
    """Request model for executing a workflow"""
    workflow_id: str = Field(..., description="Workflow ID to execute")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Execution parameters")
    mode: Optional[str] = Field("smart", description="Execution mode: sequential, parallel, smart")


class ExecutionResponse(BaseModel):
    """Response model for workflow execution"""
    execution_id: str
    workflow_id: str
    status: str
    successful_steps: int = 0
    failed_steps: int = 0
    total_steps: int = 0
    start_time: str
    end_time: Optional[str] = None
    results: Dict[str, Any] = {}
    errors: Dict[str, str] = {}


class ScenarioRequest(BaseModel):
    """Request model for running a scenario"""
    scenario_name: str = Field(..., description="Scenario name to run")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Scenario parameters")


class IntegrationStatusResponse(BaseModel):
    """Response model for integration status"""
    service: str
    status: str
    auth_type: Optional[str] = None
    capabilities: List[str] = []
    rate_limits: Optional[Dict[str, Any]] = None
    last_checked: Optional[str] = None


class ResourceMappingRequest(BaseModel):
    """Request model for resource mapping"""
    resource_type: str = Field(..., description="Type of resource to map")
    external_ids: Dict[str, str] = Field(..., description="External IDs from different services")
    source_of_truth: Optional[str] = Field(None, description="Primary source of truth")


class ResourceMappingResponse(BaseModel):
    """Response model for resource mapping"""
    uaw_id: str
    resource_type: str
    external_ids: Dict[str, str]
    source_of_truth: str
    mapped_resources: Dict[str, Any] = {}


class AuditLogRequest(BaseModel):
    """Request model for audit log query"""
    event_type: Optional[str] = Field(None, description="Filter by event type")
    resource_type: Optional[str] = Field(None, description="Filter by resource type")
    resource_id: Optional[str] = Field(None, description="Filter by resource ID")
    user_id: Optional[str] = Field(None, description="Filter by user ID")
    start_time: Optional[str] = Field(None, description="Start time filter")
    end_time: Optional[str] = Field(None, description="End time filter")
    limit: int = Field(100, description="Maximum number of results")


class AuditLogEntry(BaseModel):
    """Model for audit log entry"""
    id: str
    timestamp: str
    event_type: str
    resource_type: str
    resource_id: str
    action: str
    user_id: Optional[str] = None
    status: str
    details: Dict[str, Any] = {}


# Enums
class ExecutionMode(str, Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    SMART = "smart"


# API Endpoints
@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    components = {
        "uaw_core": "healthy",
        "state_manager": "healthy" if state_manager._initialized else "unhealthy",
        "resource_mapper": "healthy" if resource_mapper._initialized else "unhealthy",
        "security_manager": "healthy",
        "audit_logger": "healthy" if audit_logger._initialized else "unhealthy",
        "integration_registry": "healthy" if integration_registry._initialized else "unhealthy",
        "adapter_registry": "healthy" if adapter_registry._initialized else "unhealthy",
        "workflow_engine": "healthy",
        "task_orchestrator": "healthy"
    }
    
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        components=components
    )


@app.post("/api/parse", response_model=ParseResponse)
async def parse_request(request: ParseRequest):
    """Parse a natural language request"""
    try:
        # Log the request
        audit_logger.log_event(
            event_type=AuditEventType.REQUEST_PARSED,
            resource_type="request",
            resource_id=str(uuid.uuid4()),
            action="parse",
            user_id=request.user_id or "anonymous",
            details={"request": request.request}
        )
        
        # Parse the request
        parsed = uaw_core.parse_request(request.request)
        
        # Build workflow plan
        workflow_plan = None
        if parsed.get('intent') and parsed.get('action'):
            workflow_plan = uaw_core.build_workflow_plan(parsed)
        
        return ParseResponse(
            intent=parsed.get('intent', ''),
            action=parsed.get('action', ''),
            entities=parsed.get('entities', {}),
            parameters=parsed.get('parameters', {}),
            confidence=parsed.get('confidence', 0.0),
            workflow_plan=workflow_plan
        )
    
    except Exception as e:
        audit_logger.log_event(
            event_type=AuditEventType.ERROR,
            resource_type="request",
            resource_id=str(uuid.uuid4()),
            action="parse",
            user_id=request.user_id or "anonymous",
            status="failed",
            details={"error": str(e)}
        )
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/workflows", response_model=WorkflowResponse)
async def create_workflow(request: WorkflowCreateRequest):
    """Create a new workflow"""
    try:
        # Generate workflow ID
        workflow_id = f"workflow_{uuid.uuid4().hex[:8]}"
        
        # Convert steps to WorkflowStep objects
        workflow_steps = []
        for i, step in enumerate(request.steps):
            workflow_step = WorkflowStep(
                uaw_id=f"{workflow_id}_step_{i+1}",
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
            uaw_id=workflow_id,
            name=request.name,
            description=request.description,
            steps=workflow_steps,
            status=WorkflowStatus.DRAFT,
            created_at=datetime.utcnow().isoformat()
        )
        
        # Store workflow
        workflows_store[workflow_id] = workflow
        
        # Log the creation
        audit_logger.log_event(
            event_type=AuditEventType.WORKFLOW_CREATED,
            resource_type="workflow",
            resource_id=workflow_id,
            action="create",
            user_id="system",
            details={"name": request.name, "steps": len(workflow_steps)}
        )
        
        return WorkflowResponse(
            id=workflow_id,
            name=workflow.name,
            description=workflow.description,
            status=workflow.status.value,
            steps=[s.to_dict() for s in workflow.steps],
            created_at=workflow.created_at
        )
    
    except Exception as e:
        audit_logger.log_event(
            event_type=AuditEventType.ERROR,
            resource_type="workflow",
            resource_id=str(uuid.uuid4()),
            action="create",
            status="failed",
            details={"error": str(e)}
        )
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/workflows", response_model=List[WorkflowResponse])
async def list_workflows():
    """List all workflows"""
    try:
        workflows = []
        for workflow_id, workflow in workflows_store.items():
            workflows.append(WorkflowResponse(
                id=workflow_id,
                name=workflow.name,
                description=workflow.description,
                status=workflow.status.value,
                steps=[s.to_dict() for s in workflow.steps],
                created_at=workflow.created_at,
                updated_at=workflow.updated_at
            ))
        
        return workflows
    
    except Exception as e:
        audit_logger.log_event(
            event_type=AuditEventType.ERROR,
            resource_type="workflow",
            action="list",
            status="failed",
            details={"error": str(e)}
        )
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/workflows/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(workflow_id: str):
    """Get a specific workflow"""
    try:
        if workflow_id not in workflows_store:
            raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")
        
        workflow = workflows_store[workflow_id]
        
        return WorkflowResponse(
            id=workflow_id,
            name=workflow.name,
            description=workflow.description,
            status=workflow.status.value,
            steps=[s.to_dict() for s in workflow.steps],
            created_at=workflow.created_at,
            updated_at=workflow.updated_at
        )
    
    except Exception as e:
        audit_logger.log_event(
            event_type=AuditEventType.ERROR,
            resource_type="workflow",
            resource_id=workflow_id,
            action="get",
            status="failed",
            details={"error": str(e)}
        )
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/workflows/{workflow_id}/execute", response_model=ExecutionResponse)
async def execute_workflow(
    workflow_id: str,
    request: WorkflowExecutionRequest,
    background_tasks: BackgroundTasks
):
    """Execute a workflow"""
    try:
        if workflow_id not in workflows_store:
            raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")
        
        workflow = workflows_store[workflow_id]
        
        # Generate execution ID
        execution_id = f"exec_{uuid.uuid4().hex[:8]}"
        
        # Set execution mode
        if request.mode == ExecutionMode.PARALLEL.value:
            workflow_engine.execution_mode = ExecutionMode.PARALLEL
        elif request.mode == ExecutionMode.SEQUENTIAL.value:
            workflow_engine.execution_mode = ExecutionMode.SEQUENTIAL
        else:
            workflow_engine.execution_mode = ExecutionMode.SMART
        
        # Execute workflow asynchronously
        def run_workflow():
            try:
                result = asyncio.run(workflow_engine.execute_workflow(
                    workflow,
                    parameters=request.parameters or {}
                ))
                execution_results[execution_id] = result
                
                # Log completion
                audit_logger.log_event(
                    event_type=AuditEventType.WORKFLOW_COMPLETED,
                    resource_type="workflow_execution",
                    resource_id=execution_id,
                    action="execute",
                    status="completed",
                    details={
                        "workflow_id": workflow_id,
                        "successful_steps": result.successful_steps,
                        "failed_steps": result.failed_steps
                    }
                )
            
            except Exception as e:
                # Log failure
                audit_logger.log_event(
                    event_type=AuditEventType.WORKFLOW_FAILED,
                    resource_type="workflow_execution",
                    resource_id=execution_id,
                    action="execute",
                    status="failed",
                    details={"error": str(e)}
                )
                raise e
        
        # Run in background
        background_tasks.add_task(run_workflow)
        
        # Log start
        audit_logger.log_event(
            event_type=AuditEventType.WORKFLOW_STARTED,
            resource_type="workflow_execution",
            resource_id=execution_id,
            action="execute",
            status="started",
            details={"workflow_id": workflow_id, "mode": request.mode}
        )
        
        return ExecutionResponse(
            execution_id=execution_id,
            workflow_id=workflow_id,
            status="started",
            total_steps=len(workflow.steps),
            start_time=datetime.utcnow().isoformat()
        )
    
    except Exception as e:
        audit_logger.log_event(
            event_type=AuditEventType.ERROR,
            resource_type="workflow_execution",
            resource_id=str(uuid.uuid4()),
            action="execute",
            status="failed",
            details={"error": str(e)}
        )
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/executions/{execution_id}", response_model=ExecutionResponse)
async def get_execution(execution_id: str):
    """Get execution status"""
    try:
        if execution_id not in execution_results:
            raise HTTPException(status_code=404, detail=f"Execution {execution_id} not found")
        
        result = execution_results[execution_id]
        
        return ExecutionResponse(
            execution_id=execution_id,
            workflow_id=result.workflow_id,
            status=result.status.value,
            successful_steps=result.successful_steps,
            failed_steps=result.failed_steps,
            total_steps=result.total_steps,
            start_time=result.start_time,
            end_time=result.end_time,
            results=result.results,
            errors=result.errors
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/scenarios/{scenario_name}", response_model=Dict[str, Any])
async def run_scenario(scenario_name: str, request: ScenarioRequest):
    """Run a predefined scenario"""
    try:
        scenarios = {
            "first_skvoznoy": FirstSkvoznoyScenario,
            "bug_fix": FirstSkvoznoyScenario,
        }
        
        if scenario_name not in scenarios:
            raise HTTPException(
                status_code=404,
                detail=f"Scenario {scenario_name} not found. Available: {', '.join(scenarios.keys())}"
            )
        
        scenario_class = scenarios[scenario_name]
        scenario = scenario_class(
            uaw_core=uaw_core,
            state_manager=state_manager,
            resource_mapper=resource_mapper,
            security_manager=security_manager,
            audit_logger=audit_logger,
            integration_registry=integration_registry,
            adapter_registry=adapter_registry
        )
        
        # Run the scenario
        result = asyncio.run(scenario.run(**request.parameters or {}))
        
        # Log the execution
        audit_logger.log_event(
            event_type=AuditEventType.SCENARIO_EXECUTED,
            resource_type="scenario",
            resource_id=scenario_name,
            action="execute",
            status=result.get('status', 'completed'),
            details=result
        )
        
        return result
    
    except Exception as e:
        audit_logger.log_event(
            event_type=AuditEventType.ERROR,
            resource_type="scenario",
            resource_id=scenario_name,
            action="execute",
            status="failed",
            details={"error": str(e)}
        )
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/integrations", response_model=List[IntegrationStatusResponse])
async def list_integrations():
    """List all available integrations"""
    try:
        integrations = []
        
        # MCP Integrations
        mcp_integrations = integration_registry.list_integrations()
        for name, integration in mcp_integrations.items():
            integrations.append(IntegrationStatusResponse(
                service=name,
                status=integration.status.value,
                auth_type=integration.auth_type.value if hasattr(integration, 'auth_type') else None,
                capabilities=[cap.name for cap in integration.capabilities] if hasattr(integration, 'capabilities') else [],
                rate_limits=integration.rate_limits.to_dict() if hasattr(integration, 'rate_limits') else None
            ))
        
        # REST Adapters
        rest_adapters = adapter_registry.list_adapters()
        for name, adapter in rest_adapters.items():
            integrations.append(IntegrationStatusResponse(
                service=name,
                status=adapter.status.value,
                auth_type=adapter.auth_type.value if hasattr(adapter, 'auth_type') else None,
                capabilities=[cap.name for cap in adapter.capabilities] if hasattr(adapter, 'capabilities') else [],
                rate_limits=adapter.rate_limits.to_dict() if hasattr(adapter, 'rate_limits') else None
            ))
        
        return integrations
    
    except Exception as e:
        audit_logger.log_event(
            event_type=AuditEventType.ERROR,
            resource_type="integration",
            action="list",
            status="failed",
            details={"error": str(e)}
        )
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/integrations/{service}", response_model=IntegrationStatusResponse)
async def get_integration_status(service: str):
    """Get status of a specific integration"""
    try:
        # Check MCP integration
        mcp_integration = integration_registry.get_integration(service)
        if mcp_integration:
            return IntegrationStatusResponse(
                service=service,
                status=mcp_integration.status.value,
                auth_type=mcp_integration.auth_type.value if hasattr(mcp_integration, 'auth_type') else None,
                capabilities=[cap.name for cap in mcp_integration.capabilities] if hasattr(mcp_integration, 'capabilities') else [],
                rate_limits=mcp_integration.rate_limits.to_dict() if hasattr(mcp_integration, 'rate_limits') else None
            )
        
        # Check REST adapter
        rest_adapter = adapter_registry.get_adapter(service)
        if rest_adapter:
            return IntegrationStatusResponse(
                service=service,
                status=rest_adapter.status.value,
                auth_type=rest_adapter.auth_type.value if hasattr(rest_adapter, 'auth_type') else None,
                capabilities=[cap.name for cap in rest_adapter.capabilities] if hasattr(rest_adapter, 'capabilities') else [],
                rate_limits=rest_adapter.rate_limits.to_dict() if hasattr(rest_adapter, 'rate_limits') else None
            )
        
        raise HTTPException(status_code=404, detail=f"Integration {service} not found")
    
    except Exception as e:
        audit_logger.log_event(
            event_type=AuditEventType.ERROR,
            resource_type="integration",
            resource_id=service,
            action="get",
            status="failed",
            details={"error": str(e)}
        )
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/resources/map", response_model=ResourceMappingResponse)
async def map_resource(request: ResourceMappingRequest):
    """Map resources across different services"""
    try:
        # Create a UAW identifier
        uaw_id = resource_mapper.generate_uaw_id(
            request.resource_type,
            request.external_ids
        )
        
        # Map the resource
        mapped = resource_mapper.map_resource(
            resource_type=request.resource_type,
            external_ids=request.external_ids,
            source_of_truth=request.source_of_truth or list(request.external_ids.keys())[0]
        )
        
        # Log the mapping
        audit_logger.log_event(
            event_type=AuditEventType.RESOURCE_MAPPED,
            resource_type=request.resource_type,
            resource_id=uaw_id,
            action="map",
            status="completed",
            details={
                "external_ids": request.external_ids,
                "source_of_truth": mapped.source_of_truth
            }
        )
        
        return ResourceMappingResponse(
            uaw_id=uaw_id,
            resource_type=request.resource_type,
            external_ids=mapped.external_ids,
            source_of_truth=mapped.source_of_truth,
            mapped_resources=mapped.to_dict()
        )
    
    except Exception as e:
        audit_logger.log_event(
            event_type=AuditEventType.ERROR,
            resource_type=request.resource_type,
            action="map",
            status="failed",
            details={"error": str(e)}
        )
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/resources/{resource_id}", response_model=ResourceMappingResponse)
async def get_resource_mapping(resource_id: str):
    """Get resource mapping by UAW ID"""
    try:
        mapped = resource_mapper.get_resource_mapping(resource_id)
        if not mapped:
            raise HTTPException(status_code=404, detail=f"Resource {resource_id} not found")
        
        return ResourceMappingResponse(
            uaw_id=resource_id,
            resource_type=mapped.resource_type,
            external_ids=mapped.external_ids,
            source_of_truth=mapped.source_of_truth,
            mapped_resources=mapped.to_dict()
        )
    
    except Exception as e:
        audit_logger.log_event(
            event_type=AuditEventType.ERROR,
            resource_type="resource",
            resource_id=resource_id,
            action="get",
            status="failed",
            details={"error": str(e)}
        )
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/audit", response_model=List[AuditLogEntry])
async def get_audit_logs(request: AuditLogRequest):
    """Get audit logs"""
    try:
        # Get logs from audit logger
        logs = audit_logger.get_events(
            event_type=request.event_type,
            resource_type=request.resource_type,
            resource_id=request.resource_id,
            user_id=request.user_id,
            start_time=request.start_time,
            end_time=request.end_time,
            limit=request.limit
        )
        
        # Convert to response format
        entries = []
        for log in logs:
            entries.append(AuditLogEntry(
                id=log.uaw_id,
                timestamp=log.timestamp,
                event_type=log.event_type,
                resource_type=log.resource_type,
                resource_id=log.resource_id,
                action=log.action,
                user_id=log.user,
                status=log.status,
                details=log.details
            ))
        
        return entries
    
    except Exception as e:
        audit_logger.log_event(
            event_type=AuditEventType.ERROR,
            resource_type="audit_log",
            action="query",
            status="failed",
            details={"error": str(e)}
        )
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats")
async def get_stats():
    """Get UAW statistics"""
    try:
        stats = {
            "total_workflows": len(workflows_store),
            "total_executions": len(execution_results),
            "integrations": {
                "mcp": len(integration_registry.list_integrations()),
                "rest": len(adapter_registry.list_adapters())
            },
            "state_manager": {
                "active_states": len(state_manager._states)
            },
            "resource_mapper": {
                "mapped_resources": len(resource_mapper._resource_map)
            },
            "audit_logger": {
                "total_events": len(audit_logger._events)
            }
        }
        
        return JSONResponse(content=stats)
    
    except Exception as e:
        audit_logger.log_event(
            event_type=AuditEventType.ERROR,
            resource_type="stats",
            action="get",
            status="failed",
            details={"error": str(e)}
        )
        raise HTTPException(status_code=500, detail=str(e))


# Main entry point
if __name__ == "__main__":
    import uvicorn
    
    # Run the API server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        access_log=True
    )
