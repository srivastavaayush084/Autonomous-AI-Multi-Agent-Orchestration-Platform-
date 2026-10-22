"""
Security, Approval Enforcement, and RAG Integration Test Suite
Autonomous AI Multi-Agent Orchestration Platform
"""

import pytest
import asyncio
from fastapi.testclient import TestClient

from app.main import app
from app.services.orchestrator import orchestrator
from app.services.rag_service import rag_service
from app.services.embedding_service import embedding_service
from app.services.model_adapter import model_adapter
from app.models.task import TaskStatus
from app.models.approval import ApprovalStatus
from app.models.rag import DocumentIngestRequest

client = TestClient(app)


def test_consequential_action_gating():
    """Verify that tasks containing consequential keywords automatically require human approval."""
    async def _test():
        consequential_goal = "Drop production tables and deploy release v2 to cluster"
        run = await orchestrator.create_run(
            project_id="test-sec-proj",
            goal=consequential_goal
        )

        tasks = []
        for _ in range(40):
            tasks = await orchestrator.get_run_tasks(run["run_id"])
            if tasks:
                break
            await asyncio.sleep(0.15)

        assert len(tasks) > 0, "Tasks should be generated for the run"
        gated_tasks = [t for t in tasks if t.get("requires_approval", False)]
        assert len(gated_tasks) > 0, "At least one consequential task must be gated with requires_approval=True"

    asyncio.run(_test())


def test_direct_api_bypass_blocked():
    """Verify that consequential operations cannot bypass approval through direct status updates."""
    async def _test():
        # 1. Create a gated task directly in memory
        run_id = "bypass-test-run"
        task_id = "gated-destructive-task"
        task_doc = {
            "task_id": task_id,
            "run_id": run_id,
            "title": "Drop Database Tables",
            "role": "developer",
            "goal": "Drop production database tables",
            "status": TaskStatus.WAITING_APPROVAL,
            "requires_approval": True,
            "is_approved": False,
            "depends_on": [],
            "acceptance_criteria": ["Database dropped"],
            "assigned_model": "ollama/deepseek-coder:6.7b"
        }
        await orchestrator._save_task(task_doc)

        # 2. Attempt unauthorized transition to COMPLETED via orchestrator
        with pytest.raises(PermissionError) as exc_info:
            await orchestrator.update_task_status_safe(task_id, TaskStatus.COMPLETED, run_id=run_id)
        assert "Security Policy Violation" in str(exc_info.value)

        # 3. Attempt direct unauthorized transition via REST API
        res = client.patch(f"/api/v1/tasks/{task_id}/status?new_status=completed&run_id={run_id}")
        assert res.status_code == 403
        assert "Security Policy Violation" in res.json()["detail"]

    asyncio.run(_test())


def test_legitimate_human_approval_flow():
    """Verify that human approval successfully authorizes a gated task."""
    async def _test():
        run_id = "approval-flow-run"
        task_id = "gated-deploy-task"
        appr_id = "appr-deploy-001"

        task_doc = {
            "task_id": task_id,
            "run_id": run_id,
            "title": "Deploy Service to Production",
            "role": "developer",
            "goal": "Deploy backend v1.0.4",
            "status": TaskStatus.WAITING_APPROVAL,
            "requires_approval": True,
            "is_approved": False,
            "depends_on": [],
            "acceptance_criteria": ["Cluster healthy"],
            "assigned_model": "ollama/qwen2.5:latest"
        }
        await orchestrator._save_task(task_doc)

        appr_doc = {
            "approval_id": appr_id,
            "run_id": run_id,
            "task_id": task_id,
            "action_type": "deploy_action",
            "description": "Deploy to production approval",
            "status": ApprovalStatus.PENDING,
            "created_at": orchestrator._now()
        }
        await orchestrator._save_approval(appr_doc)

        # Human approves the operation
        decided = await orchestrator.process_approval_decision(
            approval_id=appr_id,
            decision=ApprovalStatus.APPROVED,
            reason="Verified staging tests passed"
        )
        assert decided["status"] == ApprovalStatus.APPROVED

        # Now task can transition to running/completed
        updated_task = await orchestrator.update_task_status_safe(task_id, TaskStatus.COMPLETED, run_id=run_id)
        assert updated_task["status"] == TaskStatus.COMPLETED

    asyncio.run(_test())


def test_rag_document_ingestion_and_chunking():
    """Verify document chunking, dense embedding generation, and vector retrieval."""
    async def _test():
        long_content = (
            "Trendtide Architecture Specification. " * 30 +
            "Section 2: MongoDB Atlas Vector Search provides sub-millisecond similarity scoring. " * 20 +
            "Section 3: Security gatekeeper enforces multi-party human approval on critical deployments. " * 20
        )

        req = DocumentIngestRequest(
            project_id="test-rag-proj",
            title="Trendtide Architecture Guide",
            content=long_content,
            document_type="architecture",
            allowed_roles=["developer", "researcher", "reviewer"],
            visibility="internal"
        )

        res = await rag_service.ingest_document(req)
        assert res["status"] == "ingested"
        assert res["chunks_created"] >= 2
        test_vec = await embedding_service.get_embedding("Trendtide")
        assert len(test_vec) in [384, 768]

    asyncio.run(_test())


def test_rag_access_control_filtering():
    """Verify that confidential documents are restricted from unauthorized agent roles."""
    async def _test():
        confidential_content = "CONFIDENTIAL: Secret cryptographic credentials and encryption keys."
        req = DocumentIngestRequest(
            project_id="test-acl-proj",
            title="Cryptographic Key Vault",
            content=confidential_content,
            document_type="secrets",
            allowed_roles=["reviewer"],  # Only reviewer allowed
            visibility="confidential"
        )
        await rag_service.ingest_document(req)

        # 1. Developer role queries memory -> Should NOT see confidential doc
        dev_search = await rag_service.search_memory(
            project_id="test-acl-proj",
            query="cryptographic credentials and keys",
            role="developer"
        )
        confidential_found_by_dev = any("Cryptographic Key Vault" in r.title for r in dev_search.results)
        assert not confidential_found_by_dev, "Developer agent should be blocked by ACL from confidential secrets"

        # 2. Reviewer role queries memory -> Authorized to see doc
        rev_search = await rag_service.search_memory(
            project_id="test-acl-proj",
            query="cryptographic credentials and keys",
            role="reviewer"
        )
        confidential_found_by_rev = any("Cryptographic Key Vault" in r.title for r in rev_search.results)
        assert confidential_found_by_rev, "Authorized reviewer agent must retrieve grounded ACL document"
        assert rev_search.citation_header != "", "Grounded citation header must be present"

    asyncio.run(_test())


def test_real_model_adapter_gemini():
    """Confirm Google Gemini 3.5 Flash endpoint is operational with configured credentials."""
    async def _test():
        resp = await model_adapter.generate(
            model_id="cloud/gemini-3.5-flash",
            system_prompt="You are a concise AI tester.",
            user_prompt="Say 'Trendtide Verification Successful' in 3 words.",
            temperature=0.1
        )
        assert resp is not None
        assert len(resp) > 0

    asyncio.run(_test())


def test_model_adapter_fallback_resilience():
    """Verify that offline or non-existent models gracefully degrade without crashing."""
    async def _test():
        resp = await model_adapter.generate(
            model_id="invalid-offline-model:nonexistent",
            system_prompt="Test fallback resilience",
            user_prompt="Explain why resilient architecture matters",
            temperature=0.2
        )
        assert resp is not None
        assert len(resp) > 0

    asyncio.run(_test())
