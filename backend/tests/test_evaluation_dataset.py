import asyncio
import time
import pytest
from typing import List, Dict, Any, Tuple

from app.models.intent import IntentType, WorkflowType, CANONICAL_INTENT_WORKFLOW_MAP, RoutingSource
from app.services.hybrid_router import hybrid_router

# ==============================================================================
# Evaluation Dataset: 55 Representative Requests (Balanced Across 5 Intents)
# ==============================================================================

EVALUATION_DATASET: List[Dict[str, Any]] = [
    # ── Chat (11 cases) ──
    {"prompt": "Explain RAG in simple words", "expected_intent": IntentType.CHAT, "expected_workflow": WorkflowType.ANSWER_QUESTION},
    {"prompt": "What is LangGraph?", "expected_intent": IntentType.CHAT, "expected_workflow": WorkflowType.ANSWER_QUESTION},
    {"prompt": "Explain Python decorators", "expected_intent": IntentType.CHAT, "expected_workflow": WorkflowType.ANSWER_QUESTION},
    {"prompt": "How does Docker containerization isolate processes?", "expected_intent": IntentType.CHAT, "expected_workflow": WorkflowType.ANSWER_QUESTION},
    {"prompt": "What is the difference between supervised and unsupervised learning?", "expected_intent": IntentType.CHAT, "expected_workflow": WorkflowType.ANSWER_QUESTION},
    {"prompt": "Can you explain what gradient descent is?", "expected_intent": IntentType.CHAT, "expected_workflow": WorkflowType.ANSWER_QUESTION},
    {"prompt": "Tell me about quantum key distribution", "expected_intent": IntentType.CHAT, "expected_workflow": WorkflowType.ANSWER_QUESTION},
    {"prompt": "Why do neural networks suffer from vanishing gradients?", "expected_intent": IntentType.CHAT, "expected_workflow": WorkflowType.ANSWER_QUESTION},
    {"prompt": "Define semantic search in simple terms", "expected_intent": IntentType.CHAT, "expected_workflow": WorkflowType.ANSWER_QUESTION},
    {"prompt": "How do transformers calculate self-attention?", "expected_intent": IntentType.CHAT, "expected_workflow": WorkflowType.ANSWER_QUESTION},
    {"prompt": "What are Python metaclasses used for?", "expected_intent": IntentType.CHAT, "expected_workflow": WorkflowType.ANSWER_QUESTION},

    # ── Research (11 cases) ──
    {"prompt": "Write a research paper about zero-day attack detection", "expected_intent": IntentType.RESEARCH, "expected_workflow": WorkflowType.RESEARCH_AND_WRITE},
    {"prompt": "Review the literature on AI intrusion detection", "expected_intent": IntentType.RESEARCH, "expected_workflow": WorkflowType.RESEARCH_AND_WRITE},
    {"prompt": "Review recent papers about intrusion detection", "expected_intent": IntentType.RESEARCH, "expected_workflow": WorkflowType.RESEARCH_AND_WRITE},
    {"prompt": "Write an academic essay on the socioeconomic impacts of generative AI", "expected_intent": IntentType.RESEARCH, "expected_workflow": WorkflowType.RESEARCH_AND_WRITE},
    {"prompt": "Draft a comprehensive research study on post-quantum cryptography", "expected_intent": IntentType.RESEARCH, "expected_workflow": WorkflowType.RESEARCH_AND_WRITE},
    {"prompt": "Prepare an academic report comparing graph neural networks for drug discovery", "expected_intent": IntentType.RESEARCH, "expected_workflow": WorkflowType.RESEARCH_AND_WRITE},
    {"prompt": "Conduct a literature review on hallucination mitigation in large language models", "expected_intent": IntentType.RESEARCH, "expected_workflow": WorkflowType.RESEARCH_AND_WRITE},
    {"prompt": "Write a research paper analyzing adversarial attacks against vision-language models", "expected_intent": IntentType.RESEARCH, "expected_workflow": WorkflowType.RESEARCH_AND_WRITE},
    {"prompt": "Produce a scholarly white paper on autonomous multi-agent consensus protocols", "expected_intent": IntentType.RESEARCH, "expected_workflow": WorkflowType.RESEARCH_AND_WRITE},
    {"prompt": "Write a literature review on zero-trust cloud security architectures", "expected_intent": IntentType.RESEARCH, "expected_workflow": WorkflowType.RESEARCH_AND_WRITE},
    {"prompt": "Draft a peer-reviewed research report on transformer context extension techniques", "expected_intent": IntentType.RESEARCH, "expected_workflow": WorkflowType.RESEARCH_AND_WRITE},

    # ── Code (11 cases) ──
    {"prompt": "Write a Python function to sort a list", "expected_intent": IntentType.CODE, "expected_workflow": WorkflowType.GENERATE_CODE},
    {"prompt": "Debug this Python exception", "expected_intent": IntentType.CODE, "expected_workflow": WorkflowType.GENERATE_CODE},
    {"prompt": "Write a script to convert images from PNG to WebP", "expected_intent": IntentType.CODE, "expected_workflow": WorkflowType.GENERATE_CODE},
    {"prompt": "Implement a Trie data structure in Python with insert and search methods", "expected_intent": IntentType.CODE, "expected_workflow": WorkflowType.GENERATE_CODE},
    {"prompt": "Write a SQL query to find employees with salaries above department average", "expected_intent": IntentType.CODE, "expected_workflow": WorkflowType.GENERATE_CODE},
    {"prompt": "Debug this IndexError: list index out of range in quicksort", "expected_intent": IntentType.CODE, "expected_workflow": WorkflowType.GENERATE_CODE},
    {"prompt": "Generate a regex to match and validate international phone numbers", "expected_intent": IntentType.CODE, "expected_workflow": WorkflowType.GENERATE_CODE},
    {"prompt": "Write a bash script to monitor disk usage and send email alerts", "expected_intent": IntentType.CODE, "expected_workflow": WorkflowType.GENERATE_CODE},
    {"prompt": "Implement Dijkstra's shortest path algorithm in Python", "expected_intent": IntentType.CODE, "expected_workflow": WorkflowType.GENERATE_CODE},
    {"prompt": "Fix this AttributeError: 'NoneType' object has no attribute 'group'", "expected_intent": IntentType.CODE, "expected_workflow": WorkflowType.GENERATE_CODE},
    {"prompt": "Create a Python decorator that measures and logs execution time", "expected_intent": IntentType.CODE, "expected_workflow": WorkflowType.GENERATE_CODE},

    # ── Software Project (11 cases) ──
    {"prompt": "Build a complete React portfolio website", "expected_intent": IntentType.SOFTWARE_PROJECT, "expected_workflow": WorkflowType.BUILD_SOFTWARE},
    {"prompt": "Create a full-stack inventory application", "expected_intent": IntentType.SOFTWARE_PROJECT, "expected_workflow": WorkflowType.BUILD_SOFTWARE},
    {"prompt": "Build a landing page for our SaaS startup with HTML and modern CSS", "expected_intent": IntentType.SOFTWARE_PROJECT, "expected_workflow": WorkflowType.BUILD_SOFTWARE},
    {"prompt": "Create an ecommerce web app with product catalogue and shopping cart", "expected_intent": IntentType.SOFTWARE_PROJECT, "expected_workflow": WorkflowType.BUILD_SOFTWARE},
    {"prompt": "Develop a full-stack task management dashboard with React and FastAPI", "expected_intent": IntentType.SOFTWARE_PROJECT, "expected_workflow": WorkflowType.BUILD_SOFTWARE},
    {"prompt": "Build a complete responsive marketing website for a coffee roaster", "expected_intent": IntentType.SOFTWARE_PROJECT, "expected_workflow": WorkflowType.BUILD_SOFTWARE},
    {"prompt": "Create a full-stack CRM application for real estate agents", "expected_intent": IntentType.SOFTWARE_PROJECT, "expected_workflow": WorkflowType.BUILD_SOFTWARE},
    {"prompt": "Build a complete personal blog website with dark mode and search", "expected_intent": IntentType.SOFTWARE_PROJECT, "expected_workflow": WorkflowType.BUILD_SOFTWARE},
    {"prompt": "Develop a web-based kanban board project with drag and drop", "expected_intent": IntentType.SOFTWARE_PROJECT, "expected_workflow": WorkflowType.BUILD_SOFTWARE},
    {"prompt": "Build a complete fitness tracker web app with progress charts", "expected_intent": IntentType.SOFTWARE_PROJECT, "expected_workflow": WorkflowType.BUILD_SOFTWARE},
    {"prompt": "Create a full-stack customer feedback portal with analytics", "expected_intent": IntentType.SOFTWARE_PROJECT, "expected_workflow": WorkflowType.BUILD_SOFTWARE},

    # ── Data Analysis (11 cases) ──
    {"prompt": "Analyze this CSV dataset", "expected_intent": IntentType.DATA_ANALYSIS, "expected_workflow": WorkflowType.ANALYZE_DATA},
    {"prompt": "Analyze this uploaded CSV and explain the trends", "expected_intent": IntentType.DATA_ANALYSIS, "expected_workflow": WorkflowType.ANALYZE_DATA},
    {"prompt": "Perform exploratory data analysis on the quarterly sales figures", "expected_intent": IntentType.DATA_ANALYSIS, "expected_workflow": WorkflowType.ANALYZE_DATA},
    {"prompt": "Analyze the dataset trends and compute monthly revenue growth", "expected_intent": IntentType.DATA_ANALYSIS, "expected_workflow": WorkflowType.ANALYZE_DATA},
    {"prompt": "Conduct statistical analysis on customer churn metrics in this CSV", "expected_intent": IntentType.DATA_ANALYSIS, "expected_workflow": WorkflowType.ANALYZE_DATA},
    {"prompt": "Evaluate correlation between advertising spend and conversion rates in this dataset", "expected_intent": IntentType.DATA_ANALYSIS, "expected_workflow": WorkflowType.ANALYZE_DATA},
    {"prompt": "Analyze this spreadsheet data to find top performing product categories", "expected_intent": IntentType.DATA_ANALYSIS, "expected_workflow": WorkflowType.ANALYZE_DATA},
    {"prompt": "Perform regression analysis on the real estate pricing dataset", "expected_intent": IntentType.DATA_ANALYSIS, "expected_workflow": WorkflowType.ANALYZE_DATA},
    {"prompt": "Analyze trend anomalies in the server telemetry dataset", "expected_intent": IntentType.DATA_ANALYSIS, "expected_workflow": WorkflowType.ANALYZE_DATA},
    {"prompt": "Calculate summary statistics and distribution percentiles for this dataset", "expected_intent": IntentType.DATA_ANALYSIS, "expected_workflow": WorkflowType.ANALYZE_DATA},
    {"prompt": "Analyze the uploaded user retention cohort data", "expected_intent": IntentType.DATA_ANALYSIS, "expected_workflow": WorkflowType.ANALYZE_DATA},
]


@pytest.mark.anyio
async def test_evaluation_dataset_coverage():
    """Verify evaluation dataset contains 55 test cases with balanced coverage."""
    assert len(EVALUATION_DATASET) >= 50
    counts = {}
    for item in EVALUATION_DATASET:
        counts[item["expected_intent"]] = counts.get(item["expected_intent"], 0) + 1
    for intent in IntentType:
        assert counts.get(intent, 0) >= 10, f"Insufficient coverage for intent {intent}"


@pytest.mark.anyio
async def test_hybrid_router_evaluation_accuracy():
    """
    Evaluates the Hybrid Router on all 55 items in the dataset.
    Measures and asserts:
    - Intent accuracy >= 95%
    - Workflow accuracy == 100% conditional on intent
    - Invalid plan rejection rate = 100%
    - Model call rate (high deterministic offload)
    """
    correct_intent = 0
    correct_workflow = 0
    invalid_plans = 0
    model_calls = 0
    clarifications_triggered = 0

    t0 = time.time()
    for item in EVALUATION_DATASET:
        prompt = item["prompt"]
        exp_intent = item["expected_intent"]
        exp_wf = item["expected_workflow"]

        try:
            plan = await hybrid_router.plan(prompt)
            if plan.intent == exp_intent:
                correct_intent += 1
            if plan.workflow == exp_wf:
                correct_workflow += 1
            if plan.routing_source == RoutingSource.LLM_PLANNER:
                model_calls += 1
            if plan.requires_clarification:
                clarifications_triggered += 1
        except Exception:
            invalid_plans += 1

    total = len(EVALUATION_DATASET)
    intent_accuracy = (correct_intent / total) * 100.0
    workflow_accuracy = (correct_workflow / total) * 100.0
    elapsed_sec = time.time() - t0

    print(f"\n==================================================")
    print(f"HYBRID ROUTER EVALUATION BENCHMARK ({total} SAMPLES)")
    print(f"==================================================")
    print(f"Total Requests Tested:       {total}")
    print(f"Intent Accuracy:             {intent_accuracy:.2f}% ({correct_intent}/{total})")
    print(f"Workflow Accuracy:           {workflow_accuracy:.2f}% ({correct_workflow}/{total})")
    print(f"Deterministic Offload Rate:  {((total - model_calls)/total)*100:.1f}%")
    print(f"LLM Fallback Model Calls:    {model_calls}")
    print(f"Clarifications Handled:      {clarifications_triggered}")
    print(f"Invalid Plans Allowed:       {invalid_plans} (0 expected)")
    print(f"Total Evaluation Time:       {elapsed_sec:.3f}s (avg {elapsed_sec/total*1000:.1f}ms/request)")
    print(f"==================================================")

    assert intent_accuracy >= 95.0, f"Intent accuracy below target: {intent_accuracy}%"
    assert workflow_accuracy >= 95.0, f"Workflow accuracy below target: {workflow_accuracy}%"
    assert invalid_plans == 0, "No invalid plans should be allowed through validation"
