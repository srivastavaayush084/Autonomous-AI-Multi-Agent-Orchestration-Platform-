from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    WAITING_APPROVAL = "waiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    NEEDS_REVIEW = "needs_review"


class AgentRole(str, Enum):
    PLANNER = "planner"
    RESEARCHER = "researcher"
    DEVELOPER = "developer"
    ANALYST = "analyst"
    WRITER = "writer"
    REVIEWER = "reviewer"


class TaskCreate(BaseModel):
    task_id: str
    run_id: str
    title: str
    role: AgentRole
    goal: str
    depends_on: List[str] = Field(default_factory=list)
    acceptance_criteria: List[str] = Field(default_factory=list)
    requires_approval: bool = False
    estimated_complexity: str = "medium"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TaskResponse(BaseModel):
    task_id: str
    run_id: str
    title: str
    role: AgentRole
    goal: str
    status: TaskStatus
    depends_on: List[str] = Field(default_factory=list)
    acceptance_criteria: List[str] = Field(default_factory=list)
    requires_approval: bool = False
    assigned_model: Optional[str] = None
    routing_reason: Optional[str] = None
    router_confidence: Optional[float] = None
    attempts: int = 0
    max_attempts: int = 3
    result_summary: Optional[str] = None
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    execution_time_seconds: Optional[float] = None
    created_at: datetime
    updated_at: datetime
