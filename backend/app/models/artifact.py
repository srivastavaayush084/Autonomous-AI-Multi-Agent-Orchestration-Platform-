from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class ArtifactType(str):
    MARKDOWN = "markdown"
    CODE = "code"
    JSON = "json"
    LOG = "log"
    REPORT = "report"


class ArtifactResponse(BaseModel):
    artifact_id: str
    run_id: str
    task_id: str
    title: str
    artifact_type: str
    file_path: Optional[str] = None
    content_snippet: Optional[str] = None
    full_content: Optional[str] = None          # complete AI response text
    is_user_facing: bool = True                 # False = internal QA/log, hidden from user
    size_bytes: int = 0
    created_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)
