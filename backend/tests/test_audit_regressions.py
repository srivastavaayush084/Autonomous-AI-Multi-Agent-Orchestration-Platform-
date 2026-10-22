"""
Production-Readiness Audit Regression Test Suite
Autonomous AI Multi-Agent Orchestration Platform

Tests:
1. CORS strict origin whitelisting without wildcard credentials
2. RAG duplicate document ingestion prevention and idempotent replacement
3. Document and project deletion cascading
4. Project isolation in vector retrieval
5. Data sovereignty confidentiality guard against cloud egress
6. Checkpoint recovery on interrupted runs
"""

import pytest
import asyncio
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.services.orchestrator import orchestrator
from app.services.rag_service import rag_service
from app.services.router import model_router
from app.models.rag import DocumentIngestRequest
from app.models.task import TaskStatus
from app.models.run import RunStatus

client = TestClient(app)


def test_cors_origin_whitelisting():
    """Verify that CORS strictly whitelists permitted origins and rejects unauthorized origins."""
    assert "*" not in settings.CORS_ORIGINS, "Security Defect: Wildcard CORS origin '*' cannot be configured"
    assert "http://localhost:5173" in settings.CORS_ORIGINS, "Frontend origin must be explicitly whitelisted"

    # Test valid origin returns Allow-Origin
    res_valid = client.options("/health", headers={
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "GET"
    })
    assert res_valid.headers.get("access-control-allow-origin") == "http://localhost:5173"

    # Test unauthorized origin is not reflected as allowed
    res_evil = client.options("/health", headers={
        "Origin": "http://malicious-site.example",
        "Access-Control-Request-Method": "GET"
    })
    assert res_evil.headers.get("access-control-allow-origin") != "http://malicious-site.example"
    assert res_evil.headers.get("access-control-allow-origin") != "*"


def test_rag_duplicate_ingestion_prevention():
    """Verify that re-ingesting an identical document updates cleanly without duplicate chunk explosion."""
    async def _test():
        proj_id = "test-dedup-proj"
        req = DocumentIngestRequest(
            project_id=proj_id,
            title="Idempotency Guide",
            content="This document must be ingested idempotently without duplicating vectors.",
            visibility="internal"
        )

        # 1. First Ingestion
        res1 = await rag_service.ingest_document(req)
        doc_id1 = res1["document_id"]
        chunks1 = res1["chunks_created"]

        # 2. Duplicate Ingestion with identical content and title
        res2 = await rag_service.ingest_document(req)
        doc_id2 = res2["document_id"]
        chunks2 = res2["chunks_created"]

        assert doc_id1 == doc_id2, "Re-ingesting identical document should update the existing document ID"
        
        # Verify total chunks in memory for this project does not double
        matching_chunks = [c for c in rag_service.mem_chunks if c.get("project_id") == proj_id]
        assert len(matching_chunks) == chunks1, f"Expected {chunks1} chunks, but found {len(matching_chunks)} (duplicate chunks detected)"

    asyncio.run(_test())


def test_rag_document_and_project_deletion():
    """Verify document deletion and complete project deletion cascading."""
    async def _test():
        proj_id = "test-delete-cascade-proj"
        # Ingest document
        req = DocumentIngestRequest(
            project_id=proj_id,
            title="Ephemeral Document",
            content="Temporary confidential data that must be purged upon deletion.",
            visibility="internal"
        )
        res = await rag_service.ingest_document(req)
        doc_id = res["document_id"]

        # Search should find it
        search_before = await rag_service.search_memory(proj_id, "Temporary confidential data")
        assert any(r.document_id == doc_id for r in search_before.results)

        # 1. Delete single document
        deleted = await rag_service.delete_document(proj_id, doc_id)
        assert deleted is True

        search_after_doc = await rag_service.search_memory(proj_id, "Temporary confidential data")
        assert not any(r.document_id == doc_id for r in search_after_doc.results), "Deleted document must not appear in search results"

        # 2. Test Project Deletion Cascade
        proj = await orchestrator.create_project(name="Cascade Target Project", description="Testing full purge")
        p_id = proj["project_id"]
        run = await orchestrator.create_run(project_id=p_id, goal="Test run for cascade deletion")
        
        # Ingest a RAG doc for this project
        await rag_service.ingest_document(DocumentIngestRequest(
            project_id=p_id,
            title="Project Document",
            content="Document inside cascade project."
        ))

        # Delete project
        proj_deleted = await orchestrator.delete_project(p_id)
        assert proj_deleted is True

        # Verify project is gone
        assert await orchestrator.get_project(p_id) is None
        assert await orchestrator.get_run(run["run_id"]) is None
        assert len(await rag_service.list_project_documents(p_id)) == 0

    asyncio.run(_test())


def test_project_isolation_in_vector_retrieval():
    """Verify that Project A vector search never returns documents from Project B."""
    async def _test():
        proj_a = "proj-isolation-alpha"
        proj_b = "proj-isolation-beta"

        # Ingest into Project A
        await rag_service.ingest_document(DocumentIngestRequest(
            project_id=proj_a,
            title="Alpha Architecture",
            content="Alpha cluster runs microservices on Kubernetes.",
            visibility="internal"
        ))

        # Ingest into Project B
        await rag_service.ingest_document(DocumentIngestRequest(
            project_id=proj_b,
            title="Beta Architecture",
            content="Beta cluster runs serverless functions on Cloud Run.",
            visibility="internal"
        ))

        # Search Project A for Beta terms -> should return 0 results from Beta
        res_a = await rag_service.search_memory(proj_a, "Cloud Run serverless functions")
        assert not any("Beta Architecture" in r.title for r in res_a.results), "Cross-project data leakage: Project A retrieved Project B documents"

        # Search Project B for Alpha terms -> should return 0 results from Alpha
        res_b = await rag_service.search_memory(proj_b, "Kubernetes microservices")
        assert not any("Alpha Architecture" in r.title for r in res_b.results), "Cross-project data leakage: Project B retrieved Project A documents"

    asyncio.run(_test())


def test_data_sovereignty_guard():
    """Verify that confidential tasks cannot be routed to public cloud LLMs."""
    # A task with high complexity would normally route to cloud/gemini-3.5-flash
    confidential_task = {
        "role": "developer",
        "goal": "Refactor proprietary cryptographic signature validation algorithms",
        "estimated_complexity": "high",
        "confidential": True,
        "requires_approval": False
    }

    model_id, reason, conf = model_router.route_task(confidential_task)
    assert not any(p in model_id.lower() for p in ["cloud", "gemini", "openai", "huggingface"]), \
        f"Data Sovereignty Violation: Confidential task was routed to cloud model {model_id}"
    assert "ollama" in model_id, "Confidential task must be routed to on-premise local model"
    assert "Data Sovereignty Guard" in reason


def test_checkpoint_recovery():
    """Verify that an interrupted run can resume from its last completed state."""
    async def _test():
        proj = await orchestrator.create_project(name="Recovery Test Project")
        run = await orchestrator.create_run(project_id=proj["project_id"], goal="Perform checkpoint recovery test")
        run_id = run["run_id"]

        # Simulate an interrupted run with 1 completed task and 1 running task
        task1 = {
            "task_id": "T1-done",
            "run_id": run_id,
            "title": "Completed Task",
            "role": "researcher",
            "goal": "Gather preliminary data",
            "status": TaskStatus.COMPLETED,
            "depends_on": []
        }
        task2 = {
            "task_id": "T2-interrupted",
            "run_id": run_id,
            "title": "Interrupted Task",
            "role": "developer",
            "goal": "Build code while process stopped",
            "status": TaskStatus.RUNNING,
            "depends_on": ["T1-done"]
        }
        await orchestrator._save_task(task1)
        await orchestrator._save_task(task2)

        # Trigger checkpoint recovery
        resumed_run = await orchestrator.resume_run(run_id)
        assert resumed_run is not None
        assert resumed_run["status"] == RunStatus.RUNNING

        # Task 2 should be reset from RUNNING to PENDING so it can be re-executed
        t2 = await orchestrator.get_task("T2-interrupted", run_id=run_id)
        assert t2["status"] == TaskStatus.PENDING, "Interrupted running task should be reset to PENDING for safe restart"

        # Task 1 must remain COMPLETED
        t1 = await orchestrator.get_task("T1-done", run_id=run_id)
        assert t1["status"] == TaskStatus.COMPLETED, "Completed task checkpoint must be preserved"

    asyncio.run(_test())
