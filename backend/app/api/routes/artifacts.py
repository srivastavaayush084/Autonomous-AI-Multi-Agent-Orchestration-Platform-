from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import PlainTextResponse, JSONResponse
from app.models.artifact import ArtifactResponse
from app.services.orchestrator import orchestrator

router = APIRouter()


@router.get("/", response_model=List[ArtifactResponse])
async def list_artifacts(run_id: Optional[str] = Query(None)):
    return await orchestrator.list_artifacts(run_id=run_id)


@router.get("/{artifact_id}")
async def get_artifact(artifact_id: str):
    """Return a single artifact with its full content."""
    items = await orchestrator.list_artifacts()
    for item in items:
        if item.get("artifact_id") == artifact_id:
            return item
    raise HTTPException(status_code=404, detail="Artifact not found")


@router.get("/{artifact_id}/content", response_class=PlainTextResponse)
async def get_artifact_content(artifact_id: str):
    """Return the full text content of an artifact."""
    items = await orchestrator.list_artifacts()
    for item in items:
        if item.get("artifact_id") == artifact_id:
            content = item.get("full_content") or item.get("content_snippet") or ""
            return PlainTextResponse(content=content, media_type="text/plain")
    raise HTTPException(status_code=404, detail="Artifact not found")


@router.get("/{artifact_id}/download")
async def download_artifact_file(artifact_id: str):
    """Download the verified physical binary file (docx, pdf, zip) if it exists."""
    import os
    from fastapi.responses import FileResponse
    items = await orchestrator.list_artifacts()
    for item in items:
        if item.get("artifact_id") == artifact_id:
            fp = item.get("file_path")
            if fp and os.path.exists(fp) and os.path.isfile(fp):
                filename = os.path.basename(fp)
                return FileResponse(path=fp, filename=filename)
            raise HTTPException(status_code=404, detail="Physical artifact file not found on disk")
    raise HTTPException(status_code=404, detail="Artifact not found")
