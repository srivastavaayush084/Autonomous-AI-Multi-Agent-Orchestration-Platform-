from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class RunStatus(str, Enum):
    PENDING = "pending"
    PLANNING = "planning"
    RUNNING = "running"
    WAITING_APPROVAL = "waiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RunCreate(BaseModel):
    project_id: str
    goal: str = Field(..., min_length=5, max_length=2000)
    parameters: Dict[str, Any] = Field(default_factory=dict)


class RunResponse(BaseModel):
    run_id: str
    project_id: str
    goal: str
    status: RunStatus
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    execution_time_seconds: Optional[float] = None
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    pending_approvals: int = 0
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
