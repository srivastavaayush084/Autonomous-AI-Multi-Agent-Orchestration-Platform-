from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class DocumentIngestRequest(BaseModel):
    project_id: str
    title: str = Field(..., min_length=2, max_length=200)
    content: str = Field(..., min_length=10)
    source_uri: Optional[str] = "local://manual_upload"
    document_type: str = "text"  # text, markdown, code, pdf_extract
    visibility: str = "internal"  # public, internal, confidential
    allowed_roles: List[str] = Field(default_factory=lambda: ["planner", "researcher", "developer", "analyst", "writer", "reviewer"])
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DocumentChunk(BaseModel):
    chunk_id: str
    document_id: str
    project_id: str
    title: str
    chunk_index: int
    text: str
    vector: Optional[List[float]] = None
    source_uri: str
    allowed_roles: List[str]
    visibility: str
    token_count: int
    created_at: datetime


class RAGQueryRequest(BaseModel):
    project_id: str
    query: str = Field(..., min_length=3)
    role: Optional[str] = "researcher"
    top_k: int = Field(default=3, ge=1, le=10)
    min_similarity: float = Field(default=0.45, ge=0.0, le=1.0)


class RAGSearchResult(BaseModel):
    chunk_id: str
    document_id: str
    title: str
    text: str
    score: float
    source_uri: str
    chunk_index: int
    visibility: str


class RAGQueryResponse(BaseModel):
    query: str
    project_id: str
    results: List[RAGSearchResult]
    total_found: int
    citation_header: str
