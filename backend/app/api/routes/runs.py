from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from app.models.run import RunCreate, RunResponse
from app.models.task import TaskResponse
from app.services.orchestrator import orchestrator

router = APIRouter()


@router.post("/", response_model=RunResponse, status_code=201)
async def create_run(data: RunCreate):
    project = await orchestrator.get_project(data.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Referenced project does not exist")
    return await orchestrator.create_run(project_id=data.project_id, goal=data.goal, parameters=data.parameters)


@router.get("/", response_model=List[RunResponse])
async def list_runs(project_id: Optional[str] = Query(None)):
    return await orchestrator.list_runs(project_id=project_id)


@router.get("/{run_id}", response_model=RunResponse)
async def get_run(run_id: str):
    run = await orchestrator.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@router.get("/{run_id}/tasks", response_model=List[TaskResponse])
async def get_run_tasks(run_id: str):
    run = await orchestrator.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return await orchestrator.get_run_tasks(run_id)


@router.post("/{run_id}/resume", response_model=RunResponse)
async def resume_run(run_id: str):
    run = await orchestrator.resume_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found or cannot be resumed")
    return run
