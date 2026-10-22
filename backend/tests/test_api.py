import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.router import model_router

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "version" in data


def test_project_lifecycle():
    # 1. Create Project
    res = client.post("/api/v1/projects/", json={
        "name": "E-Commerce Microservice Refactor",
        "description": "Decompose and optimize legacy order processing pipeline"
    })
    assert res.status_code == 201
    proj_data = res.json()
    assert "project_id" in proj_data
    project_id = proj_data["project_id"]

    # 2. List Projects
    res = client.get("/api/v1/projects/")
    assert res.status_code == 200
    projects = res.json()
    assert any(p["project_id"] == project_id for p in projects)


def test_model_router_capabilities():
    # Test coding task routing
    code_task = {
        "role": "developer",
        "goal": "Write high-performance TypeScript microservice for Redis cache synchronization",
        "estimated_complexity": "high",
        "requires_approval": False
    }
    model_id, reason, conf = model_router.route_task(code_task)
    assert "deepseek" in model_id or "gemini" in model_id or "qwen" in model_id
    assert conf > 0.0

    # Test light writing task routing
    write_task = {
        "role": "writer",
        "goal": "Draft brief user-facing summary notes",
        "estimated_complexity": "low",
        "requires_approval": False
    }
    model_id, reason, conf = model_router.route_task(write_task)
    assert model_id is not None


def test_run_and_task_execution():
    # Create project
    p_res = client.post("/api/v1/projects/", json={
        "name": "Autonomous Test Project",
        "description": "Integration test validation run"
    })
    project_id = p_res.json()["project_id"]

    # Create run
    r_res = client.post("/api/v1/runs/", json={
        "project_id": project_id,
        "goal": "Audit cybersecurity compliance and generate structured threat report"
    })
    assert r_res.status_code == 201
    run_id = r_res.json()["run_id"]

    # Fetch run
    get_res = client.get(f"/api/v1/runs/{run_id}")
    assert get_res.status_code == 200
    assert get_res.json()["run_id"] == run_id
