import os
import json
import tempfile
import pytest
from unittest.mock import AsyncMock, patch

from app.models.intent import (
    IntentType,
    WorkflowType,
    CANONICAL_INTENT_WORKFLOW_MAP,
    ExecutionPlan,
    RoutingSource,
)
from app.services.hybrid_router import HybridRouter
from app.services.orchestrator import OrchestrationService, orchestrator


@pytest.fixture
def router():
    return HybridRouter()


# ==============================================================================
# 1. Canonical Intent and Workflow Mapping Tests (Phase 2)
# ==============================================================================

def test_canonical_intent_workflow_mapping():
    """Verify all 5 canonical intents map to their specified canonical workflows."""
    assert CANONICAL_INTENT_WORKFLOW_MAP[IntentType.CHAT] == WorkflowType.ANSWER_QUESTION
    assert CANONICAL_INTENT_WORKFLOW_MAP[IntentType.RESEARCH] == WorkflowType.RESEARCH_AND_WRITE
    assert CANONICAL_INTENT_WORKFLOW_MAP[IntentType.CODE] == WorkflowType.GENERATE_CODE
    assert CANONICAL_INTENT_WORKFLOW_MAP[IntentType.SOFTWARE_PROJECT] == WorkflowType.BUILD_SOFTWARE
    assert CANONICAL_INTENT_WORKFLOW_MAP[IntentType.DATA_ANALYSIS] == WorkflowType.ANALYZE_DATA


def test_invalid_workflow_mismatch_rejected():
    """Validation must reject any plan where intent and workflow do not match canonical mapping."""
    with pytest.raises(ValueError, match="Workflow mismatch"):
        ExecutionPlan(
            intent=IntentType.CHAT,
            workflow=WorkflowType.BUILD_SOFTWARE,
            reason="Invalid combination",
            deliverables=["markdown"],
            confidence=1.0
        )


def test_unknown_intent_rejected():
    """Pydantic must reject unknown intents."""
    with pytest.raises(ValueError):
        ExecutionPlan(
            intent="unknown_intent",  # type: ignore
            workflow=WorkflowType.ANSWER_QUESTION,
            reason="Invalid intent",
            deliverables=["markdown"]
        )


def test_unknown_workflow_rejected():
    """Pydantic must reject arbitrary model-generated workflow names."""
    with pytest.raises(ValueError):
        ExecutionPlan(
            intent=IntentType.CHAT,
            workflow="arbitrary_pipeline_v3",  # type: ignore
            reason="Invalid workflow name",
            deliverables=["markdown"]
        )


# ==============================================================================
# 2. Mandatory Regression Test Table (Phase 8)
# ==============================================================================

MANDATORY_CASES = [
    ("Explain RAG in simple words", IntentType.CHAT, WorkflowType.ANSWER_QUESTION),
    ("What is LangGraph?", IntentType.CHAT, WorkflowType.ANSWER_QUESTION),
    ("Write a research paper about zero-day attack detection", IntentType.RESEARCH, WorkflowType.RESEARCH_AND_WRITE),
    ("Review the literature on AI intrusion detection", IntentType.RESEARCH, WorkflowType.RESEARCH_AND_WRITE),
    ("Write a Python function to sort a list", IntentType.CODE, WorkflowType.GENERATE_CODE),
    ("Debug this Python exception", IntentType.CODE, WorkflowType.GENERATE_CODE),
    ("Build a complete React portfolio website", IntentType.SOFTWARE_PROJECT, WorkflowType.BUILD_SOFTWARE),
    ("Create a full-stack inventory application", IntentType.SOFTWARE_PROJECT, WorkflowType.BUILD_SOFTWARE),
    ("Analyze this CSV dataset", IntentType.DATA_ANALYSIS, WorkflowType.ANALYZE_DATA),
    ("Explain Python decorators", IntentType.CHAT, WorkflowType.ANSWER_QUESTION),
]


@pytest.mark.parametrize("prompt,expected_intent,expected_workflow", MANDATORY_CASES)
@pytest.mark.anyio
async def test_mandatory_requests_routing(router, prompt, expected_intent, expected_workflow):
    """Verify each of the 10 minimum requests from the specification routes deterministically."""
    plan = await router.plan(prompt)
    assert plan.intent == expected_intent, f"Failed for '{prompt}': expected {expected_intent}, got {plan.intent}"
    assert plan.workflow == expected_workflow, f"Failed for '{prompt}': expected {expected_workflow}, got {plan.workflow}"
    assert plan.routing_source == RoutingSource.DETERMINISTIC


# ==============================================================================
# 3. Deterministic Edge Cases & Distinction Tests (Phase 3)
# ==============================================================================

@pytest.mark.anyio
async def test_technical_topic_does_not_imply_technical_workflow(router):
    """A technical topic (e.g. RAG, Docker, Kubernetes) is still chat when asking for explanation."""
    technical_questions = [
        "What is Retrieval-Augmented Generation?",
        "Explain how Docker containers work",
        "Can you describe transformer attention mechanisms?",
        "Define gradient descent in machine learning",
        "Tell me about zero-trust architecture"
    ]
    for q in technical_questions:
        plan = await router.plan(q)
        assert plan.intent == IntentType.CHAT, f"Failed on '{q}': got {plan.intent}"
        assert plan.workflow == WorkflowType.ANSWER_QUESTION


@pytest.mark.anyio
async def test_python_mention_does_not_imply_software_project(router):
    """Mentioning a language for a snippet or bug fix routes to code, not software project."""
    code_requests = [
        "Write a Python script to parse a log file",
        "Implement a binary search function in Python",
        "Write a regex pattern for phone numbers",
        "Fix this Python TypeError: unsupported operand type"
    ]
    for r in code_requests:
        plan = await router.plan(r)
        assert plan.intent == IntentType.CODE, f"Failed on '{r}': got {plan.intent}"
        assert plan.workflow == WorkflowType.GENERATE_CODE


@pytest.mark.anyio
async def test_empty_and_whitespace_requests(router):
    """Empty and whitespace-only requests default safely to chat without errors."""
    for empty in ["", "   ", "\n\t  "]:
        plan = await router.plan(empty)
        assert plan.intent == IntentType.CHAT
        assert plan.workflow == WorkflowType.ANSWER_QUESTION


# ==============================================================================
# 4. Deliverable Format Requirements & Non-Interference (Phase 3)
# ==============================================================================

@pytest.mark.anyio
async def test_explicit_format_requirements_without_confusing_intent(router):
    """Explicit formats (PDF, DOCX, ZIP) must be recognized in deliverables without altering intent."""
    # Chat with PDF requirement
    p1 = await router.plan("Explain RAG in simple words as a PDF")
    assert p1.intent == IntentType.CHAT
    assert "pdf" in p1.deliverables

    # Research with DOCX requirement
    p2 = await router.plan("Write a research paper about zero-day attacks in docx format")
    assert p2.intent == IntentType.RESEARCH
    assert "docx" in p2.deliverables

    # Software project with ZIP requirement
    p3 = await router.plan("Build a complete React portfolio website and package as a zip archive")
    assert p3.intent == IntentType.SOFTWARE_PROJECT
    assert "zip" in p3.deliverables


# ==============================================================================
# 5. Data Analysis Validation & Clarification (Phase 5 & 6)
# ==============================================================================

@pytest.mark.anyio
async def test_data_analysis_requires_attachment_or_clarification(router):
    """Data analysis requires data access; if missing, requires_clarification is True."""
    # No attachments or data provided -> clarification required
    plan_missing = await router.plan("Analyze this uploaded CSV and explain the trends")
    assert plan_missing.intent == IntentType.DATA_ANALYSIS
    assert plan_missing.requires_clarification is True
    assert plan_missing.clarification_message is not None

    # Attachments provided -> ready to execute
    plan_with_data = await router.plan(
        "Analyze this uploaded CSV and explain the trends",
        attachments=["financial_metrics_2026.csv"]
    )
    assert plan_with_data.intent == IntentType.DATA_ANALYSIS
    assert plan_with_data.requires_clarification is False


# ==============================================================================
# 6. Constrained LLM Planning & Resilience (Phase 4)
# ==============================================================================

@pytest.mark.anyio
async def test_llm_planner_with_mocked_valid_json(router):
    """LLM planner correctly parses structured output for ambiguous prompts."""
    mock_response = {
        "intent": "research",
        "workflow": "research_and_write",
        "deliverables": ["report"],
        "reason": "Request asks for academic synthesis of emerging papers",
        "confidence": 0.88
    }

    with patch("app.services.model_adapter.model_adapter.chat_structured", new_callable=AsyncMock) as mock_chat:
        mock_chat.return_value = mock_response
        # Ambiguous prompt with no deterministic keywords
        plan = await router.plan("Emerging paradigms in distributed consensus protocols")
        assert plan.intent == IntentType.RESEARCH
        assert plan.workflow == WorkflowType.RESEARCH_AND_WRITE
        assert plan.routing_source == RoutingSource.LLM_PLANNER


@pytest.mark.anyio
async def test_llm_planner_enforces_canonical_workflow_on_mismatch(router):
    """If the LLM returns an invalid intent/workflow pair, canonical mapping is enforced."""
    # LLM hallucinates an invalid combination: chat with research_and_write
    mismatched_response = {
        "intent": "chat",
        "workflow": "research_and_write",
        "reason": "Model confused simple question with research",
        "confidence": 0.70
    }

    with patch("app.services.model_adapter.model_adapter.chat_structured", new_callable=AsyncMock) as mock_chat:
        mock_chat.return_value = mismatched_response
        plan = await router.plan("Complex philosophical inquiry on epistemology")
        # Validator must correct workflow to answer_question
        assert plan.intent == IntentType.CHAT
        assert plan.workflow == WorkflowType.ANSWER_QUESTION


@pytest.mark.anyio
async def test_llm_planner_handles_markdown_code_fences():
    """Model adapter strips markdown code fences around JSON outputs."""
    from app.services.model_adapter import model_adapter
    # Simulate Ollama returning markdown code fences
    raw_markdown = '```json\n{"intent": "code", "workflow": "generate_code", "reason": "script request"}\n```'
    
    from unittest.mock import MagicMock
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"message": {"content": raw_markdown}}
        mock_post.return_value = mock_resp

        result = await model_adapter.chat_structured("ollama/llama3.2:1b", "sys", "user")
        assert result.get("intent") == "code"
        assert result.get("workflow") == "generate_code"


@pytest.mark.anyio
async def test_llm_planner_timeout_falls_back_safely(router):
    """If Ollama is unavailable or times out, the router falls back safely without unhandled exception."""
    import httpx

    with patch("app.services.model_adapter.model_adapter.chat_structured", new_callable=AsyncMock) as mock_chat:
        mock_chat.side_effect = httpx.ReadTimeout("Ollama read timed out")
        # Ambiguous prompt
        plan = await router.plan("General systems discussion on latency")
        assert plan.routing_source == RoutingSource.FALLBACK
        assert plan.intent == IntentType.CHAT
        assert plan.workflow == WorkflowType.ANSWER_QUESTION


# ==============================================================================
# 7. Artifact Physical Verification Tests (Phase 7)
# ==============================================================================

@pytest.mark.anyio
async def test_physical_artifact_verification(router):
    """Artifact registration rejects non-existent or empty physical files."""
    svc = OrchestrationService()
    run_id = "test-art-verify-run"

    # 1. Non-existent file path must NOT be registered as a valid physical download
    art1 = await svc._register_artifact(
        run_id=run_id,
        task_id="t1",
        title="Fake Download",
        artifact_type="pdf",
        content="Text content",
        file_path="C:/non/existent/path/fake.pdf"
    )
    assert art1["file_path"] is None, "Non-existent file path should be omitted from artifact"

    # 2. Existing real file must be verified and registered
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tf:
        tf.write(b"Real verified content on disk")
        temp_path = tf.name

    try:
        art2 = await svc._register_artifact(
            run_id=run_id,
            task_id="t2",
            title="Real Download",
            artifact_type="text",
            content="Real verified content on disk",
            file_path=temp_path
        )
        assert art2["file_path"] == temp_path
        assert art2["size_bytes"] > 0
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@pytest.mark.anyio
async def test_quoted_and_numbered_prompts_route_accurately(router):
    """
    Verify that user requests containing leading list numbers (e.g. '1. ')
    and curly/straight quotes route accurately according to intent.
    """
    # 1. Numbered & curly quoted software project request
    prompt_web = '1. “Build a complete responsive React portfolio website and provide the source code as a ZIP.”'
    plan_web = await router.plan(prompt_web)
    assert plan_web.intent == IntentType.SOFTWARE_PROJECT
    assert plan_web.workflow == WorkflowType.BUILD_SOFTWARE
    assert "zip" in plan_web.deliverables

    # 2. Numbered & quoted research request
    prompt_res = '1. "Write a research paper on AI-based zero-day attack detection and provide DOCX and PDF files."'
    plan_res = await router.plan(prompt_res)
    assert plan_res.intent == IntentType.RESEARCH
    assert plan_res.workflow == WorkflowType.RESEARCH_AND_WRITE
    assert "docx" in plan_res.deliverables
    assert "pdf" in plan_res.deliverables

    # 3. Numbered & quoted direct answer request
    prompt_chat = '1. “Explain RAG in simple words with one example.”'
    plan_chat = await router.plan(prompt_chat)
    assert plan_chat.intent == IntentType.CHAT
    assert plan_chat.workflow == WorkflowType.ANSWER_QUESTION

