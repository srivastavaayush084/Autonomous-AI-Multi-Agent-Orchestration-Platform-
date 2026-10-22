from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
import uuid


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    description: Optional[str] = Field(default="", max_length=1000)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ProjectResponse(BaseModel):
    project_id: str
    name: str
    description: str
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)
