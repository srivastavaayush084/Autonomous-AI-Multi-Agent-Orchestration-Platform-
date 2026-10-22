from fastapi import APIRouter, HTTPException
from app.models.task import TaskResponse
from app.services.orchestrator import orchestrator

router = APIRouter()


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str):
    task = await orchestrator.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.patch("/{task_id}/status", response_model=TaskResponse)
async def update_task_status(task_id: str, new_status: str):
    try:
        from app.models.task import TaskStatus
        status_enum = TaskStatus(new_status)
        return await orchestrator.update_task_status_safe(task_id, status_enum)
    except PermissionError as pe:
        raise HTTPException(status_code=403, detail=str(pe))
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
