from typing import List
from fastapi import APIRouter, HTTPException
from app.models.project import ProjectCreate, ProjectResponse
from app.services.orchestrator import orchestrator

router = APIRouter()


@router.post("/", response_model=ProjectResponse, status_code=201)
async def create_project(data: ProjectCreate):
    return await orchestrator.create_project(name=data.name, description=data.description, metadata=data.metadata)


@router.get("/", response_model=List[ProjectResponse])
async def list_projects():
    return await orchestrator.list_projects()


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str):
    proj = await orchestrator.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    return proj


@router.delete("/{project_id}")
async def delete_project(project_id: str):
    deleted = await orchestrator.delete_project(project_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Project not found or already deleted")
    return {"status": "deleted", "project_id": project_id}
