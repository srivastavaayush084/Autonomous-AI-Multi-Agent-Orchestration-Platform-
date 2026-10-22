from fastapi import APIRouter
from app.api.routes import projects, runs, tasks, models, approvals, artifacts, rag

api_router = APIRouter()

api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(runs.router, prefix="/runs", tags=["runs"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
api_router.include_router(models.router, prefix="/models", tags=["models"])
api_router.include_router(approvals.router, prefix="/approvals", tags=["approvals"])
api_router.include_router(artifacts.router, prefix="/artifacts", tags=["artifacts"])
api_router.include_router(rag.router, prefix="/rag", tags=["rag"])
