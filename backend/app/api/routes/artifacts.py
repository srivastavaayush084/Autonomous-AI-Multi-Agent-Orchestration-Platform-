from typing import List, Optional
from fastapi import APIRouter, Query
from app.models.artifact import ArtifactResponse
from app.services.orchestrator import orchestrator

router = APIRouter()


@router.get("/", response_model=List[ArtifactResponse])
async def list_artifacts(run_id: Optional[str] = Query(None)):
    return await orchestrator.list_artifacts(run_id=run_id)
