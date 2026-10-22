from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ApprovalRequest(BaseModel):
    approval_id: str
    run_id: str
    task_id: str
    action_type: str  # e.g., "file_write", "deploy", "destructive_command", "external_api"
    description: str
    risk_level: RiskLevel = RiskLevel.MEDIUM
    status: ApprovalStatus = ApprovalStatus.PENDING
    payload: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    decided_at: Optional[datetime] = None
    decided_by: Optional[str] = None
    decision_reason: Optional[str] = None


class ApprovalDecision(BaseModel):
    decision: ApprovalStatus  # APPROVED or REJECTED
    decided_by: str = "human_operator"
    reason: Optional[str] = None
