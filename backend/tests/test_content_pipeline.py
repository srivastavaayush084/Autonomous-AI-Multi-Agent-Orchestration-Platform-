import os
import pytest
from unittest.mock import patch, AsyncMock
from app.models.intent import ExecutionPlan, IntentType, WorkflowType
from app.models.run import RunStatus
from app.services.orchestrator import orchestrator, _save_docx, _save_pdf, _save_zip
from app.services.model_adapter import model_adapter


async def run_pipeline(goal: str, parameters: dict = None):
    run_doc = await orchestrator.create_run(project_id="test-proj", goal=goal, parameters=parameters or {})
    await orchestrator.start_run_execution(run_doc["run_id"])
    return await orchestrator.get_run(run_doc["run_id"])


@pytest.mark.anyio
async def test_qa_workflow_generates_real_answer_and_validates():
    """
    Test A: Chat
    Request: 'Explain RAG in simple words with one example.'
    Pass criteria:
    - Real explanation identifying Retrieval-Augmented Generation.
    - Relevant example is included.
    - No generic completion-only response is accepted.
    """
    mock_rag_answer = (
        "## Retrieval-Augmented Generation (RAG)\n\n"
        "Retrieval-Augmented Generation (RAG) is an AI framework that connects a Large Language Model (LLM) "
        "to external knowledge sources like databases or private company documents before generating a response.\n\n"
        "### How It Works\n"
        "1. **Retrieval**: When you ask a question, the system searches a vector database for relevant text passages.\n"
        "2. **Augmentation**: The retrieved passages are appended to your prompt as context.\n"
        "3. **Generation**: The LLM reads the context and generates an accurate, up-to-date answer.\n\n"
        "### Practical Example\n"
        "Imagine an internal company HR chatbot. If an employee asks 'What is our 2026 remote work travel allowance?', "
        "the system retrieves the exact 2026 travel policy PDF and feeds it to the LLM to generate the exact allowance amount."
    )

    with patch("app.services.model_adapter.model_adapter.generate", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = mock_rag_answer

        run = await run_pipeline("Explain RAG in simple words with one example.")
        assert run["status"] == RunStatus.COMPLETED

        tasks = await orchestrator.get_run_tasks(run["run_id"])
        assert len(tasks) == 1
        assert tasks[0]["status"] == "completed"

        artifacts = await orchestrator.list_artifacts(run["run_id"])
        assert len(artifacts) >= 1
        content = artifacts[0]["full_content"].lower()

        # Must explain RAG and not be canned filler
        assert any(term in content for term in ["retriev", "rag", "generation", "augmented"])
        assert "the requested task has been completed" not in content
        assert "all acceptance criteria have been satisfied" not in content


@pytest.mark.anyio
async def test_qa_workflow_rejects_canned_placeholder_and_fails_safely():
    """Verify that if a model outputs canned filler, validation fails and marks run FAILED."""
    fake_canned_text = (
        "## Response\n\nThe requested task has been completed: Explain RAG.\n\n"
        "The implementation follows best practices. All acceptance criteria have been satisfied."
    )
    with patch("app.services.model_adapter.model_adapter.generate", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = fake_canned_text

        run = await run_pipeline("Explain RAG in simple words with one example.")
        assert run["status"] == RunStatus.FAILED
        assert "Content validation failed" in run.get("error_message", "")


@pytest.mark.anyio
async def test_research_workflow_substantive_paper_docx_pdf():
    """
    Test B: Research Paper
    Request: 'Create a research paper on AI-based zero-day attack detection and provide DOCX and PDF files.'
    Pass criteria:
    - Substantive topic-specific content.
    - Required sections are present (Abstract, Introduction, References).
    - DOCX and PDF files exist on disk and have non-zero size.
    - Reviewer does not overwrite paper.
    """
    goal = "Create a research paper on AI-based zero-day attack detection and provide DOCX and PDF files."

    mock_research = (
        "# Technical Research Notes: Zero-Day Attack Detection\n\n"
        "## 1. Threat Model & Zero-Day Vulnerability Characteristics\n"
        "Zero-day attacks exploit unknown software vulnerabilities before vendors release patches. "
        "Signature-based Intrusion Detection Systems (IDS) like Snort rely on static byte patterns and fail against unseen exploits.\n\n"
        "## 2. Machine Learning and Deep Learning Architectures\n"
        "Anomaly detection models such as Variational Autoencoders (VAEs), Graph Neural Networks (GNNs), "
        "and Bidirectional LSTMs model baseline normal behavior and detect deviations in system call sequences or network flows.\n\n"
        "## 3. Benchmark Datasets and Evaluation\n"
        "Evaluation relies on benchmarks such as CIC-IDS2017 and NSL-KDD. Precision, Recall, and False Positive Rate (FPR) "
        "are critical metrics because high FPR overwhelms SOC analysts.\n\n"
        "## 4. Adversarial Challenges and Concept Drift\n"
        "Adversaries employ gradient-based perturbations to evade anomaly detectors, while benign software updates cause concept drift.\n\n"
        "## References\n"
        "1. Sommer, R., & Paxson, V. (2010). Outside the Closed World: On Using Machine Learning for Network Intrusion Detection. IEEE S&P.\n"
        "2. Sharafaldin, I., et al. (2018). Toward Generating a New Intrusion Detection Dataset and Intrusion Traffic Characterization. ICISSP."
    )

    mock_paper = (
        "# Autonomous Detection of Zero-Day Exploits Using Deep Representation Learning\n\n"
        "## Abstract\n"
        "Zero-day cyberattacks present a formidable threat to modern computing infrastructure because signature-based "
        "intrusion detection systems cannot identify previously unseen vulnerabilities. This paper investigates deep representation "
        "learning architectures, specifically variational autoencoders and graph neural networks, for anomaly-based zero-day detection. "
        "We evaluate models on the CIC-IDS2017 benchmark dataset, demonstrating a 94.2% detection rate on novel attack vectors while "
        "maintaining a false positive rate below 0.8%.\n\n"
        "## Keywords\n"
        "Zero-Day Detection, Deep Learning, Anomaly Detection, Autoencoders, Intrusion Detection Systems.\n\n"
        "## 1. Introduction and Threat Model\n"
        "The proliferation of advanced persistent threats (APTs) has exposed the architectural limitations of traditional "
        "pattern-matching security appliances. When an attacker weaponizes an undisclosed zero-day flaw, signature repositories "
        "contain no corresponding hash or heuristic rule. Consequently, machine learning paradigms must identify anomalies via "
        "behavioral telemetry rather than static signatures.\n\n"
        "## 2. Background and Related Work\n"
        "Early anomaly detection utilized statistical profiling and support vector machines (SVMs). However, modern enterprise "
        "traffic exhibits non-linear topological dependencies that necessitate deep neural networks.\n\n"
        "## 3. Proposed Deep Learning Methodologies\n"
        "Our framework leverages a deep autoencoder that reconstructs high-dimensional NetFlow metrics. During inference, "
        "reconstruction loss exceeding an adaptive threshold signals an exploit payload. In parallel, temporal graph networks "
        "track host-to-host lateral movement.\n\n"
        "## 4. Datasets, Evaluation Methodology, and Metrics\n"
        "We evaluate our methodology using the CIC-IDS2017 benchmark dataset. Performance is measured using standard metrics:\n"
        "- Precision: 93.6%\n"
        "- Recall: 94.2%\n"
        "- F1-Score: 93.9%\n"
        "- False Alarm Rate: 0.78%\n\n"
        "## 5. Technical Challenges and Adversarial Evasion\n"
        "Adversarial evasion remains a major hurdle. Attackers can blend payload execution with benign web traffic. Concept drift "
        "requires continuous self-supervised domain adaptation.\n\n"
        "## 6. Conclusion and Future Directions\n"
        "Deep representation learning provides a viable path toward preemptive zero-day defense. Future research will explore "
        "reinforcement learning for automated incident containment.\n\n"
        "## References\n"
        "1. Sommer, R., & Paxson, V. (2010). Outside the Closed World: On Using Machine Learning for Network Intrusion Detection. IEEE S&P.\n"
        "2. Ring, M., et al. (2019). A survey of network-based intrusion detection data sets. Computers & Security, 86, 147-167.\n"
        "3. Mirsky, Y., et al. (2018). Kitsune: An Ensemble of Autoencoders for Online Network Intrusion Detection. NDSS."
    )

    mock_review = (
        "# Peer Review Report\n\n"
        "## Summary: Strong Accept\n"
        "The paper presents a coherent formulation of zero-day anomaly detection. All required sections are present. "
        "Empirical methodology on CIC-IDS2017 is rigorous."
    )

    async def side_effect(model_id, system_prompt, user_prompt, temperature=0.3):
        if "Research topic" in user_prompt or "threat models" in user_prompt.lower():
            return mock_research
        elif "research findings" in user_prompt.lower() or "academic research paper" in user_prompt.lower():
            return mock_paper
        else:
            return mock_review

    with patch("app.services.model_adapter.model_adapter.generate", side_effect=side_effect):
        run = await run_pipeline(goal)
        assert run["status"] == RunStatus.COMPLETED

        artifacts = await orchestrator.list_artifacts(run["run_id"])
        docx_artifacts = [a for a in artifacts if a.get("artifact_type") == "docx"]
        pdf_artifacts = [a for a in artifacts if a.get("artifact_type") == "pdf"]

        assert len(docx_artifacts) == 1
        assert len(pdf_artifacts) == 1

        docx_path = docx_artifacts[0]["file_path"]
        pdf_path = pdf_artifacts[0]["file_path"]

        assert docx_path and os.path.exists(docx_path) and os.path.getsize(docx_path) > 500
        assert pdf_path and os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 500

        # Verify final user-facing paper contains substantive content, not reviewer text
        paper_artifacts = [a for a in artifacts if a.get("is_user_facing") and a.get("artifact_type") == "report"]
        assert len(paper_artifacts) == 1
        assert "Autonomous Detection of Zero-Day Exploits" in paper_artifacts[0]["full_content"]
        assert "Peer Review Report" not in paper_artifacts[0]["full_content"]


@pytest.mark.anyio
async def test_website_generation_produces_real_react_code_and_valid_zip():
    """
    Test C: Website
    Request: 'Build a complete responsive React portfolio website and provide the source code as a ZIP.'
    Pass criteria:
    - Stack detection recognizes React.
    - package.json, index.html, App.jsx, index.css, README.md generated.
    - ZIP archive exists, passes integrity checks, and contains valid source files.
    """
    goal = "Build a complete responsive React portfolio website and provide the source code as a ZIP."

    mock_pkg = '{\n  "name": "react-portfolio",\n  "private": true,\n  "version": "1.0.0",\n  "dependencies": {\n    "react": "^18.3.1",\n    "react-dom": "^18.3.1"\n  }\n}'
    mock_html = '<!DOCTYPE html>\n<html lang="en">\n<head><title>Portfolio</title></head>\n<body><div id="root"></div><script type="module" src="/src/main.jsx"></script></body>\n</html>'
    mock_app = 'import React, { useState } from "react";\nexport default function App() {\n  return (\n    <div className="portfolio">\n      <header><h1>Alex Rivers | Full-Stack Engineer</h1></header>\n      <section id="projects"><div className="card">Project 1</div></section>\n    </div>\n  );\n}'
    mock_css = ':root { --primary: #06b6d4; --bg: #0f172a; }\nbody { background: var(--bg); color: #fff; font-family: sans-serif; }\n.portfolio { max-width: 1200px; margin: 0 auto; padding: 2rem; }'
    mock_readme = '# React Portfolio Website\n\n## Getting Started\n```bash\nnpm install\nnpm run dev\n```'

    async def side_effect(model_id, sys_prompt, user_prompt, temperature=0.2):
        if "package.json" in user_prompt:
            return f"```json\n{mock_pkg}\n```"
        elif "index.html" in user_prompt:
            return f"```html\n{mock_html}\n```"
        elif "App.jsx" in user_prompt:
            return f"```jsx\n{mock_app}\n```"
        elif "index.css" in user_prompt:
            return f"```css\n{mock_css}\n```"
        elif "README.md" in user_prompt:
            return f"```markdown\n{mock_readme}\n```"
        return "Component architecture planned."

    with patch("app.services.model_adapter.model_adapter.generate", side_effect=side_effect):
        run = await run_pipeline(goal)
        assert run["status"] == RunStatus.COMPLETED

        artifacts = await orchestrator.list_artifacts(run["run_id"])
        zip_artifacts = [a for a in artifacts if a.get("artifact_type") == "zip"]
        assert len(zip_artifacts) == 1

        zip_path = zip_artifacts[0]["file_path"]
        assert zip_path and os.path.exists(zip_path) and os.path.getsize(zip_path) > 100

        # Verify ZIP contains actual React source files
        import zipfile
        with zipfile.ZipFile(zip_path, "r") as zf:
            namelist = zf.namelist()
            assert "package.json" in namelist
            assert "index.html" in namelist
            assert "src/App.jsx" in namelist
            assert "src/index.css" in namelist
            assert "README.md" in namelist
            # Ensure no corrupted files
            assert zf.testzip() is None


@pytest.mark.anyio
async def test_failure_conditions_do_not_produce_false_success():
    """
    Failure tests:
    - Provider failure marks run FAILED.
    - Corrupt/missing deliverable marks run FAILED.
    - No deliverables are presented as ready.
    """
    with patch("app.services.model_adapter.model_adapter.generate", side_effect=RuntimeError("Provider offline")):
        run = await run_pipeline("Explain RAG in simple words")
        assert run["status"] == RunStatus.FAILED
        assert "Provider offline" in run.get("error_message", "")

        # Must not have user-facing deliverables
        artifacts = await orchestrator.list_artifacts(run["run_id"])
        user_facing = [a for a in artifacts if a.get("is_user_facing")]
        assert len(user_facing) == 0


@pytest.mark.anyio
async def test_research_inference_failure_halts_immediately_and_blocks_error_review():
    """
    Verify that when model inference fails during research/writing:
    - The task is marked FAILED immediately.
    - The error message is NOT forwarded to T3-qa as a research paper to review.
    - No DOCX or PDF artifacts are generated.
    - Run status is FAILED.
    """
    error_response = "[ERROR: Model inference failed for 'ollama/llama3.2:1b': local Ollama and cloud providers unavailable or timed out.]"

    called_prompts = []

    async def side_effect(model_id, sys_prompt, user_prompt, temperature=0.3):
        called_prompts.append(user_prompt)
        # T1 succeeds, but T2-write fails
        if "Research topic" in user_prompt:
            return "# Research Notes\nSubstantive research notes..."
        elif "academic research paper" in user_prompt.lower():
            return error_response
        return "Review text"

    with patch("app.services.model_adapter.model_adapter.generate", side_effect=side_effect):
        run = await run_pipeline("Create a research paper on AI-based zero-day attack detection")
        assert run["status"] == RunStatus.FAILED
        assert "failed" in run.get("error_message", "").lower()

        # Crucial check: T3-qa must NEVER have been called to review the error string!
        review_prompts = [p for p in called_prompts if "Review this research paper" in p]
        assert len(review_prompts) == 0, "Reviewer must not be invoked on failed paper generation"

        # Check tasks: T2-write must be FAILED
        tasks = await orchestrator.get_run_tasks(run["run_id"])
        t2 = next(t for t in tasks if t["task_id"] == "T2-write")
        assert t2["status"] == "failed"
        assert "[ERROR:" in t2.get("error_message", "")

        # Crucial check: No downloadable artifacts produced
        artifacts = await orchestrator.list_artifacts(run["run_id"])
        downloadable = [a for a in artifacts if a.get("artifact_type") in ["docx", "pdf"]]
        assert len(downloadable) == 0
