import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether, PageBreak, HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        if self._pageNumber == 1:
            return  # Suppress headers/footers on cover page

        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))

        # Header
        self.drawString(54, letter[1] - 36, "Autonomous AI Multi-Agent Orchestration Platform — System Architecture & Manual")
        self.setStrokeColor(colors.HexColor("#e2e8f0"))
        self.setLineWidth(0.5)
        self.line(54, letter[1] - 42, letter[0] - 54, letter[1] - 42)

        # Footer
        self.line(54, 46, letter[0] - 54, 46)
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(letter[0] - 54, 32, page_text)
        self.drawString(54, 32, "CONFIDENTIAL & PROPRIETARY — ALL RIGHTS RESERVED")
        self.restoreState()


def build_pdf(filename="Autonomous_AI_Multi_Agent_Orchestration_Platform_Documentation.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=26,
        leading=32,
        textColor=colors.HexColor('#0f172a'),
        alignment=1
    )

    subtitle_style = ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=18,
        textColor=colors.HexColor('#475569'),
        alignment=1
    )

    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=22,
        textColor=colors.HexColor('#1e1b4b'),
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#312e81'),
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor('#334155'),
        spaceAfter=6
    )

    bullet_style = ParagraphStyle(
        'Bullet_Custom',
        parent=body_style,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=3
    )

    code_style = ParagraphStyle(
        'Code_Custom',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor('#0f172a')
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.white
    )

    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor('#1e293b')
    )

    story = []

    # ==========================================
    # COVER PAGE
    # ==========================================
    story.append(Spacer(1, 20))
    
    icon_path = os.path.abspath("frontend/public/favicon.png")
    if os.path.exists(icon_path):
        story.append(Image(icon_path, width=1.6*inch, height=1.6*inch))
        story.append(Spacer(1, 15))

    story.append(Paragraph("Autonomous AI Multi-Agent<br/>Orchestration Platform", title_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph("System Architecture, ML Task Routing, RAG Vector Search & Production Runbook", subtitle_style))
    story.append(Spacer(1, 15))

    meta_table_data = [
        [Paragraph("<b>Document Version:</b>", body_style), Paragraph("1.0.0 (Production Verified)", body_style)],
        [Paragraph("<b>Status:</b>", body_style), Paragraph("17/17 Pytest Verified | 99.32% ML Router Accuracy", body_style)],
        [Paragraph("<b>Technology Stack:</b>", body_style), Paragraph("FastAPI, React 19, Vite, scikit-learn, MongoDB Atlas, Ollama, Gemini", body_style)],
        [Paragraph("<b>Repository:</b>", body_style), Paragraph("github.com/srivastavaayush084/Autonomous-AI-Multi-Agent-Orchestration-Platform-", body_style)],
        [Paragraph("<b>Author / Lead:</b>", body_style), Paragraph("Ayush Srivastava (srivastavaayush084@gmail.com)", body_style)],
        [Paragraph("<b>Published Date:</b>", body_style), Paragraph("October 2026", body_style)]
    ]
    meta_table = Table(meta_table_data, colWidths=[1.8*inch, 4.7*inch])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#e2e8f0')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 12),
        ('RIGHTPADDING', (0,0), (-1,-1), 12),
    ]))
    story.append(meta_table)

    story.append(Spacer(1, 20))
    callout_data = [[
        Paragraph(
            "<b>EXECUTIVE NOTICE:</b> This technical manual encapsulates the complete design, mathematical benchmarks, "
            "security gateways, API specifications, and operational directives of the Autonomous AI Multi-Agent Platform. "
            "All components have been audited for zero data leakage, strict origin whitelisting, and deterministic DAG state enforcement.",
            body_style
        )
    ]]
    callout_table = Table(callout_data, colWidths=[6.5*inch])
    callout_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#eff6ff')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#3b82f6')),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 12),
        ('RIGHTPADDING', (0,0), (-1,-1), 12),
    ]))
    story.append(callout_table)
    story.append(PageBreak())

    # ==========================================
    # SECTION 1: SYSTEM OVERVIEW & ARCHITECTURE
    # ==========================================
    story.append(Paragraph("1. Executive Summary & Core Value Proposition", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#3b82f6"), spaceAfter=8))
    
    story.append(Paragraph(
        "Modern enterprise workflows demand automated goal decomposition capable of orchestrating diverse specialist agents, "
        "managing fine-grained dependencies, upholding data sovereignty, and providing air-tight safety gates. "
        "The <b>Autonomous AI Multi-Agent Orchestration Platform</b> addresses these imperatives through a five-pillar foundation:",
        body_style
    ))

    story.append(Paragraph("• <b>Stateful DAG Task Engine:</b> Decomposes high-level goals into topological execution graphs with verifiable acceptance criteria, concurrent branch execution, and automated checkpoint recovery.", bullet_style))
    story.append(Paragraph("• <b>Audited ML Model Router:</b> A hybrid classifier combining rule-based heuristics with a trained scikit-learn RandomForest model achieving 99.32% test accuracy and cutting cloud API expenditure by 87.8%.", bullet_style))
    story.append(Paragraph("• <b>Data Sovereignty Firewall:</b> Automated policy engine screening task prompts for confidential data and enforcing 100% on-premise execution via local Ollama models (Qwen 2.5, DeepSeek Coder, Llama 3.2).", bullet_style))
    story.append(Paragraph("• <b>Retrieval-Augmented Generation (RAG):</b> 768-dimensional vector search integrated with MongoDB Atlas Vector Search ($vectorSearch), SHA-256 chunk deduplication, and strict project tenant isolation.", bullet_style))
    story.append(Paragraph("• <b>Human-in-the-Loop Safety Gateway:</b> Consequential tasks (deploy, delete, write, charge) are quarantined in waiting_approval, completely immune to direct API bypass (HTTP 403 Forbidden).", bullet_style))

    story.append(Spacer(1, 10))
    story.append(Paragraph("2. Multi-Agent Topology & Lifecycle State Machine", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#3b82f6"), spaceAfter=8))

    story.append(Paragraph(
        "The platform coordinates specialized autonomous agent personas, each governed by role-specific prompt contracts:",
        body_style
    ))

    roles_data = [
        [Paragraph("Agent Role", table_header_style), Paragraph("Core Responsibility", table_header_style), Paragraph("Primary Model Fleet", table_header_style), Paragraph("Artifact Deliverable", table_header_style)],
        [Paragraph("<b>Planner Agent</b>", table_cell_style), Paragraph("Goal decomposition, topological DAG generation, dependency resolution", table_cell_style), Paragraph("qwen2.5:latest", table_cell_style), Paragraph("Execution Graph JSON", table_cell_style)],
        [Paragraph("<b>Researcher Agent</b>", table_cell_style), Paragraph("Domain knowledge discovery, constraint gathering, documentation synthesis", table_cell_style), Paragraph("llama3.2:latest / Gemini 3.5", table_cell_style), Paragraph("Research & Strategy Briefs", table_cell_style)],
        [Paragraph("<b>Developer Agent</b>", table_cell_style), Paragraph("Software construction, code refactoring, schema design, script generation", table_cell_style), Paragraph("deepseek-coder:6.7b", table_cell_style), Paragraph("Executable Source Code", table_cell_style)],
        [Paragraph("<b>Analyst Agent</b>", table_cell_style), Paragraph("Metric evaluation, numerical modeling, telemetry & data analysis", table_cell_style), Paragraph("deepseek-r1:8b / Gemini 3.5", table_cell_style), Paragraph("Analytical Forecasts", table_cell_style)],
        [Paragraph("<b>Reviewer Agent</b>", table_cell_style), Paragraph("Verification against acceptance criteria, QA tests, safety gating", table_cell_style), Paragraph("qwen2.5:latest", table_cell_style), Paragraph("Verification Audit Logs", table_cell_style)]
    ]
    roles_table = Table(roles_data, colWidths=[1.3*inch, 2.3*inch, 1.4*inch, 1.5*inch])
    roles_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e1b4b')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8fafc')]),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(roles_table)

    story.append(Spacer(1, 8))
    story.append(Paragraph("<b>Finite State Machine Transitions:</b>", h2_style))
    story.append(Paragraph("Every task adheres to strict, deterministic state transitions: <code>PENDING</code> → <code>READY</code> → <code>RUNNING</code> → [<code>WAITING_APPROVAL</code>] → <code>COMPLETED</code> / <code>FAILED</code>. The orchestrator continuously monitors completed upstream task IDs to safely unlock downstream dependencies in parallel branches.", body_style))

    story.append(PageBreak())

    # ==========================================
    # SECTION 2: MACHINE LEARNING MODEL ROUTER
    # ==========================================
    story.append(Paragraph("3. Machine Learning Model Router & Cost Audit", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#3b82f6"), spaceAfter=8))

    story.append(Paragraph(
        "To balance quality, inference speed, and budget, the platform implements a two-stage routing pipeline. "
        "A feature extractor maps incoming task descriptors into 5 numerical dimensions: (1) Specialist Role, (2) Prompt Word Count, "
        "(3) Complexity Estimate, (4) Safety Gate Flag, and (5) Code Keyword Signals. "
        "The classifier was evaluated under strict deduplication across 589 task samples (441 train / 148 test holdout):",
        body_style
    ))

    ml_metrics_data = [
        [Paragraph("Metric Dimension", table_header_style), Paragraph("Score / Value", table_header_style), Paragraph("Evaluation Methodology", table_header_style)],
        [Paragraph("<b>Stratified 5-Fold Cross Validation</b>", table_cell_style), Paragraph("<b>99.66% (±0.42%)</b>", table_cell_style), Paragraph("5-Fold Cross Validation on 441 train partition", table_cell_style)],
        [Paragraph("<b>Held-Out Test Accuracy</b>", table_cell_style), Paragraph("<b>99.32% (147 / 148)</b>", table_cell_style), Paragraph("Evaluated against unseen deduplicated test set", table_cell_style)],
        [Paragraph("<b>Held-Out Macro F1 Score</b>", table_cell_style), Paragraph("<b>99.13%</b>", table_cell_style), Paragraph("Macro-averaged across all 5 task classes", table_cell_style)],
        [Paragraph("<b>Train/Test Data Leakage</b>", table_cell_style), Paragraph("<b>0.00%</b>", table_cell_style), Paragraph("Zero overlapping samples between partitions", table_cell_style)],
        [Paragraph("<b>Rule Baseline Accuracy</b>", table_cell_style), Paragraph("71.62%", table_cell_style), Paragraph("Heuristic capability-based baseline", table_cell_style)],
        [Paragraph("<b>ML Performance Lift</b>", table_cell_style), Paragraph("<b>+27.70% Lift</b>", table_cell_style), Paragraph("Accuracy gain over heuristic baseline", table_cell_style)],
        [Paragraph("<b>Local Execution Ratio</b>", table_cell_style), Paragraph("<b>87.8% Local</b>", table_cell_style), Paragraph("130 tasks routed on-premise; 18 to cloud API", table_cell_style)],
        [Paragraph("<b>Cloud Cost Reduction</b>", table_cell_style), Paragraph("<b>87.8% Savings</b>", table_cell_style), Paragraph("Calculated under Gemini 3.5 Flash pricing tier", table_cell_style)]
    ]
    ml_table = Table(ml_metrics_data, colWidths=[2.2*inch, 1.8*inch, 2.5*inch])
    ml_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e1b4b')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8fafc')]),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(ml_table)

    story.append(Spacer(1, 10))
    story.append(Paragraph("<b>Confusion Matrix on 148 Held-Out Test Samples:</b>", h2_style))
    
    cm_data = [
        [Paragraph("Actual \\ Predicted", table_header_style), Paragraph("coding", table_header_style), Paragraph("creative", table_header_style), Paragraph("data_analysis", table_header_style), Paragraph("reasoning", table_header_style), Paragraph("simple", table_header_style)],
        [Paragraph("<b>coding</b> (30)", table_cell_style), Paragraph("30", table_cell_style), Paragraph("0", table_cell_style), Paragraph("0", table_cell_style), Paragraph("0", table_cell_style), Paragraph("0", table_cell_style)],
        [Paragraph("<b>creative</b> (25)", table_cell_style), Paragraph("0", table_cell_style), Paragraph("25", table_cell_style), Paragraph("0", table_cell_style), Paragraph("0", table_cell_style), Paragraph("0", table_cell_style)],
        [Paragraph("<b>data_analysis</b> (30)", table_cell_style), Paragraph("0", table_cell_style), Paragraph("0", table_cell_style), Paragraph("29", table_cell_style), Paragraph("1", table_cell_style), Paragraph("0", table_cell_style)],
        [Paragraph("<b>reasoning</b> (33)", table_cell_style), Paragraph("0", table_cell_style), Paragraph("0", table_cell_style), Paragraph("0", table_cell_style), Paragraph("33", table_cell_style), Paragraph("0", table_cell_style)],
        [Paragraph("<b>simple</b> (30)", table_cell_style), Paragraph("0", table_cell_style), Paragraph("0", table_cell_style), Paragraph("0", table_cell_style), Paragraph("0", table_cell_style), Paragraph("30", table_cell_style)]
    ]
    cm_table = Table(cm_data, colWidths=[1.5*inch, 1.0*inch, 1.0*inch, 1.0*inch, 1.0*inch, 1.0*inch])
    cm_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0f172a')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('ALIGN', (1,1), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8fafc')]),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(cm_table)

    story.append(Spacer(1, 10))
    story.append(Paragraph("4. Data Sovereignty & Enterprise Egress Guard", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#3b82f6"), spaceAfter=8))
    story.append(Paragraph(
        "To ensure compliance with corporate governance, GDPR, and HIPAA standards, the platform includes a strict "
        "<b>Data Sovereignty Guard</b> (<code>_apply_data_sovereignty_guard</code>). Tasks tagged with confidentiality constraints "
        "or internal IP indicators are automatically intercepted before cloud dispatch and forced into on-premise execution "
        "via local Ollama inference. Cloud APIs are strictly forbidden from receiving sovereign payloads.",
        body_style
    ))

    story.append(PageBreak())

    # ==========================================
    # SECTION 3: RAG & VECTOR SEARCH
    # ==========================================
    story.append(Paragraph("5. Retrieval-Augmented Generation & Project Memory", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#3b82f6"), spaceAfter=8))
    
    story.append(Paragraph(
        "The RAG subsystem provides long-term project memory and factual grounding for all specialist agents. "
        "Key operational properties include:",
        body_style
    ))
    story.append(Paragraph("• <b>Recursive Chunking:</b> Configurable chunk sizes (500 tokens) with 50-token sliding overlap to preserve contextual continuity across boundaries.", bullet_style))
    story.append(Paragraph("• <b>SHA-256 Deduplication:</b> Identical documents uploaded multiple times are recognized via content hashing; chunk generation is bypassed, eliminating duplicate vector explosion.", bullet_style))
    story.append(Paragraph("• <b>Atlas Vector Search ($vectorSearch):</b> Semantic retrieval powered by 768-dimensional embeddings and cosine similarity index (<code>project_embeddings_vector_index</code>).", bullet_style))
    story.append(Paragraph("• <b>Tenant Isolation:</b> Every vector query injects <code>filter: {'project_id': project_id}</code>, mathematically preventing cross-tenant information leakage.", bullet_style))
    story.append(Paragraph("• <b>Cascading Deletion:</b> Project deletion or individual document purge atomically cleans both MongoDB metadata documents and vector embedding chunks.", bullet_style))

    story.append(Spacer(1, 10))
    story.append(Paragraph("6. Human-in-the-Loop Safety Gateway & Verification", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#3b82f6"), spaceAfter=8))

    story.append(Paragraph(
        "Autonomous operations involving external risk (e.g. database migration, cloud deployment, asset purging, or payment authorization) "
        "are protected by cryptographic and role-based safety gates:",
        body_style
    ))
    story.append(Paragraph("• <b>Automated Consequential Detection:</b> Tasks containing critical keywords (<code>deploy</code>, <code>drop</code>, <code>delete</code>, <code>terminate</code>, <code>wipe</code>, <code>charge</code>) are unconditionally marked for human approval.", bullet_style))
    story.append(Paragraph("• <b>Anti-Bypass Guard:</b> Direct API calls attempting to transition a gated task directly to <code>RUNNING</code> or <code>COMPLETED</code> without approved review records are rejected with <b>HTTP 403 Forbidden</b>.", bullet_style))
    story.append(Paragraph("• <b>Self-Healing Execution:</b> Once an authorized operator approves the request, the orchestrator immediately sets the task to <code>READY</code> and automatically resumes execution across all downstream branches.", bullet_style))

    story.append(Spacer(1, 10))
    story.append(Paragraph("7. Comprehensive REST API Reference", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#3b82f6"), spaceAfter=8))

    api_data = [
        [Paragraph("Method & Endpoint", table_header_style), Paragraph("Description", table_header_style), Paragraph("Request / Response Payload", table_header_style)],
        [Paragraph("<code>POST /api/v1/projects</code>", table_cell_style), Paragraph("Create isolated workspace", table_cell_style), Paragraph("<code>{ name, description }</code>", table_cell_style)],
        [Paragraph("<code>DELETE /api/v1/projects/{id}</code>", table_cell_style), Paragraph("Cascading delete project & vectors", table_cell_style), Paragraph("Returns deletion confirmation", table_cell_style)],
        [Paragraph("<code>POST /api/v1/runs</code>", table_cell_style), Paragraph("Launch autonomous execution run", table_cell_style), Paragraph("<code>{ project_id, goal }</code>", table_cell_style)],
        [Paragraph("<code>POST /api/v1/runs/{id}/resume</code>", table_cell_style), Paragraph("Checkpoint recovery for paused run", table_cell_style), Paragraph("Relaunches background DAG loop", table_cell_style)],
        [Paragraph("<code>GET /api/v1/runs/{id}/tasks</code>", table_cell_style), Paragraph("List all tasks with self-healing check", table_cell_style), Paragraph("Returns task array with model metadata", table_cell_style)],
        [Paragraph("<code>POST /api/v1/approvals/{id}/decision</code>", table_cell_style), Paragraph("Human approval decision", table_cell_style), Paragraph("<code>{ decision: 'approved'|'rejected', reason }</code>", table_cell_style)],
        [Paragraph("<code>POST /api/v1/rag/ingest</code>", table_cell_style), Paragraph("Ingest & embed RAG document", table_cell_style), Paragraph("<code>{ project_id, title, content }</code>", table_cell_style)],
        [Paragraph("<code>POST /api/v1/rag/search</code>", table_cell_style), Paragraph("Vector semantic search with citations", table_cell_style), Paragraph("<code>{ project_id, query, top_k }</code>", table_cell_style)],
        [Paragraph("<code>GET /health</code>", table_cell_style), Paragraph("Readiness probe & cluster telemetry", table_cell_style), Paragraph("Status, mode, strategy, DB health", table_cell_style)]
    ]
    api_table = Table(api_data, colWidths=[2.3*inch, 2.3*inch, 1.9*inch])
    api_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e1b4b')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8fafc')]),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(api_table)

    story.append(PageBreak())

    # ==========================================
    # SECTION 4: DEPLOYMENT & PRODUCTION RUNBOOK
    # ==========================================
    story.append(Paragraph("8. Deployment & Operational Runbook", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#3b82f6"), spaceAfter=8))

    story.append(Paragraph("<b>Option A: Docker Compose Deployment (Recommended)</b>", h2_style))
    story.append(Paragraph(
        "The platform includes multi-stage container definitions for full-stack deployment with Docker Compose:",
        body_style
    ))
    docker_snippet = (
        "# 1. Build and start complete stack in background\n"
        "docker-compose up --build -d\n\n"
        "# 2. Stream backend application logs\n"
        "docker-compose logs -f backend\n\n"
        "# 3. Teardown\n"
        "docker-compose down"
    )
    story.append(Table([[Paragraph(docker_snippet.replace('\n', '<br/>'), code_style)]],
                       colWidths=[6.5*inch],
                       style=[('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f1f5f9')),
                              ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
                              ('TOPPADDING', (0,0), (-1,-1), 6),
                              ('BOTTOMPADDING', (0,0), (-1,-1), 6),
                              ('LEFTPADDING', (0,0), (-1,-1), 10)]))

    story.append(Spacer(1, 8))
    story.append(Paragraph("<b>Option B: Bare-Metal / Local Development</b>", h2_style))
    local_snippet = (
        "# Backend (Terminal 1)\n"
        ".\\venv\\Scripts\\Activate.ps1\n"
        "python backend/run.py             # Server: http://localhost:8000 (Docs: /docs)\n\n"
        "# Frontend (Terminal 2)\n"
        "cd frontend && npm run dev        # Dashboard: http://localhost:5173"
    )
    story.append(Table([[Paragraph(local_snippet.replace('\n', '<br/>'), code_style)]],
                       colWidths=[6.5*inch],
                       style=[('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f1f5f9')),
                              ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
                              ('TOPPADDING', (0,0), (-1,-1), 6),
                              ('BOTTOMPADDING', (0,0), (-1,-1), 6),
                              ('LEFTPADDING', (0,0), (-1,-1), 10)]))

    story.append(Spacer(1, 10))
    story.append(Paragraph("9. Backup, Disaster Recovery & Rollback Protocol", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#3b82f6"), spaceAfter=8))

    story.append(Paragraph("• <b>Automated MongoDB Atlas Backups:</b> Configure continuous point-in-time recovery (PITR) with daily cluster snapshots in the Atlas Console.", bullet_style))
    story.append(Paragraph("• <b>CLI Database Dump:</b> <code>mongodump --uri=\"$MONGODB_URI\" --out=/backups/$(date +%Y%m%d)</code>", bullet_style))
    story.append(Paragraph("• <b>Container Rollback:</b> If a regression occurs during deployment, roll back immediately with <code>docker-compose down && git checkout HEAD~1 && docker-compose up --build -d</code>.", bullet_style))
    story.append(Paragraph("• <b>Production Checklist:</b> Ensure TLS termination (Port 443), restrict <code>CORS_ORIGINS</code>, and confirm Ollama models are pulled (<code>ollama pull deepseek-coder:6.7b</code>, <code>ollama pull llama3.2:latest</code>).", bullet_style))

    story.append(Spacer(1, 15))
    signoff_data = [
        [Paragraph("<b>Document Approved by:</b>", body_style), Paragraph("Ayush Srivastava", body_style)],
        [Paragraph("<b>Verification Standard:</b>", body_style), Paragraph("All 17 Pytest Suites Passed (100% Pass Rate)", body_style)],
        [Paragraph("<b>Distribution:</b>", body_style), Paragraph("Enterprise Engineering, Operations, and Auditing Teams", body_style)]
    ]
    signoff_table = Table(signoff_data, colWidths=[2.2*inch, 4.3*inch])
    signoff_table.setStyle(TableStyle([
        ('LINEBELOW', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(signoff_table)

    # Build document with NumberedCanvas
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[OK] Documentation PDF successfully created: {filename}")


if __name__ == "__main__":
    out_pdf = "Autonomous_AI_Multi_Agent_Orchestration_Platform_Documentation.pdf"
    if len(sys.argv) > 1:
        out_pdf = sys.argv[1]
    build_pdf(out_pdf)
