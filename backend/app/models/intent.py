from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, model_validator


class IntentType(str, Enum):
    CHAT = "chat"
    RESEARCH = "research"
    CODE = "code"
    SOFTWARE_PROJECT = "software_project"
    DATA_ANALYSIS = "data_analysis"


class WorkflowType(str, Enum):
    ANSWER_QUESTION = "answer_question"
    RESEARCH_AND_WRITE = "research_and_write"
    GENERATE_CODE = "generate_code"
    BUILD_SOFTWARE = "build_software"
    ANALYZE_DATA = "analyze_data"


CANONICAL_INTENT_WORKFLOW_MAP: Dict[IntentType, WorkflowType] = {
    IntentType.CHAT: WorkflowType.ANSWER_QUESTION,
    IntentType.RESEARCH: WorkflowType.RESEARCH_AND_WRITE,
    IntentType.CODE: WorkflowType.GENERATE_CODE,
    IntentType.SOFTWARE_PROJECT: WorkflowType.BUILD_SOFTWARE,
    IntentType.DATA_ANALYSIS: WorkflowType.ANALYZE_DATA,
}

CANONICAL_WORKFLOW_INTENT_MAP: Dict[WorkflowType, IntentType] = {
    v: k for k, v in CANONICAL_INTENT_WORKFLOW_MAP.items()
}


class DeliverableFormat(str, Enum):
    MARKDOWN = "markdown"
    CODE = "code"
    DOCX = "docx"
    PDF = "pdf"
    ZIP = "zip"
    REPORT = "report"
    CSV = "csv"
    JSON = "json"


class RoutingSource(str, Enum):
    DETERMINISTIC = "deterministic"
    LLM_PLANNER = "llm_planner"
    FALLBACK = "fallback"


class TaskPlanItem(BaseModel):
    task_id: str
    title: str
    role: str
    goal: str
    depends_on: List[str] = Field(default_factory=list)
    acceptance_criteria: List[str] = Field(default_factory=list)
    requires_approval: bool = False
    estimated_complexity: str = "medium"


class ExecutionPlan(BaseModel):
    intent: IntentType
    workflow: WorkflowType
    deliverables: List[str] = Field(default_factory=list)
    reason: str
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    routing_source: RoutingSource = RoutingSource.DETERMINISTIC
    selected_agents: List[str] = Field(default_factory=list)
    tasks: List[TaskPlanItem] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)
    requires_approval: bool = False
    requires_clarification: bool = False
    clarification_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_canonical_workflow(self) -> "ExecutionPlan":
        expected_workflow = CANONICAL_INTENT_WORKFLOW_MAP.get(self.intent)
        if expected_workflow and self.workflow != expected_workflow:
            raise ValueError(
                f"Workflow mismatch: intent '{self.intent.value}' must map to canonical workflow "
                f"'{expected_workflow.value}', but got '{self.workflow.value}'"
            )
        return self


class IntentClassificationRequest(BaseModel):
    text: str = Field(..., min_length=1)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    attachments: List[str] = Field(default_factory=list)
    has_dataset: bool = False
