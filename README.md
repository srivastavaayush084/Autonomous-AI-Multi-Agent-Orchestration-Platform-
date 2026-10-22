# Autonomous AI Multi-Agent Orchestration Platform

[![FastAPI](https://img.shields.io/badge/FastAPI-v0.115+-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![React + Vite](https://img.shields.io/badge/React%2019%20%2B%20Vite-TypeScript-61DAFB?logo=react)](https://vitejs.dev/)
[![ML Router](https://img.shields.io/badge/scikit--learn-ML--Router%20(99.32%25)-F7931E?logo=scikit-learn)](https://scikit-learn.org/)
[![Database](https://img.shields.io/badge/MongoDB-Atlas%20Vector%20Search-47A248?logo=mongodb)](https://www.mongodb.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker)](https://www.docker.com/)
[![Tests](https://img.shields.io/badge/Tests-17%20Passed-brightgreen)](https://pytest.org/)

An enterprise-grade, stateful autonomous AI multi-agent orchestration platform engineered for complex goal decomposition, Directed Acyclic Graph (DAG) task scheduling, machine-learning-based model routing, retrieval-augmented generation (RAG) with MongoDB Atlas Vector Search, and a cryptographically gated human-in-the-loop approval workflow.

---

## 🏛️ System Architecture

```mermaid
graph TD
    User([User / Cybernetic Dashboard]) -->|Submit Goal| API[FastAPI Gateway]
    API -->|Persist State| DB[(MongoDB Atlas)]
    API -->|Trigger Orchestration| Orchestrator[Orchestration Engine]
    
    Orchestrator -->|Decompose Plan| Planner[Planner Agent]
    Planner -->|Task DAG & Criteria| Orchestrator
    
    Orchestrator -->|Route Task| Router[Model Router / ML Classifier]
    Router -->|Data Sovereignty Guard| Guard{Sensitive Task?}
    Guard -->|Yes: Block Cloud Egress| LocalFleet[On-Premise Ollama Fleet]
    Guard -->|No: Optimal Route| Fleet[Hybrid Inference Fleet]
    
    subgraph Agent Workers
        Researcher[Research Agent]
        Developer[Developer Agent]
        Analyst[Analyst Agent]
        Writer[Document Producer Agent]
    end
    
    Fleet --> Researcher
    Fleet --> Developer
    Fleet --> Analyst
    Fleet --> Writer
    LocalFleet --> Researcher
    LocalFleet --> Developer
    
    Agent Workers -->|Context Query| VectorDB[(Atlas Vector Search / RAG)]
    Agent Workers -->|Draft Outputs| Verifier[Reviewer & Verification Agent]
    Verifier -->|Standard Artifact| Artifacts[Artifact Store]
    Verifier -->|Consequential / Destructive Action| ApprovalQueue[Human Approval Queue]
    ApprovalQueue -->|Approved / Rejected| Orchestrator
    
    Artifacts --> DB
```

---

## 🚀 Key Features

### 1. Stateful DAG Task Engine
- Decomposes high-level goals into dependency-linked subtasks with verifiable acceptance criteria.
- Executes independent graph branches concurrently using async worker pools.
- Enforces strict finite state transitions: `pending` → `ready` → `running` → `waiting_approval` → `completed` / `failed`.
- Full checkpoint recovery support: resume interrupted or partially failed runs without repeating successful tasks.

### 2. Machine Learning Model Router (Audited)
- **Architecture**: Transparent heuristic capability baseline combined with a trained `scikit-learn` RandomForest classifier.
- **Audit Verification**:
  - **99.32% Test Accuracy** and **99.13% Macro F1 Score** on deduplicated test holdout (0.00% leakage).
  - **87.8% Cloud Cost Savings** via automated local delegation to Ollama (`llama3.2`, `deepseek-r1`).
  - **Data Sovereignty Guard**: Automatically identifies confidential/sensitive tasks and enforces zero-cloud-egress local processing.

### 3. Retrieval-Augmented Generation (RAG) & Memory
- Document ingestion pipeline with recursive text chunking and SHA-256 idempotency deduplication.
- Semantic retrieval powered by 768-dimensional embeddings and MongoDB Atlas Vector Search ($vectorSearch).
- Metadata-enforced project isolation and cascading deletion routines.

### 4. Human-in-the-Loop Safety Gateway
- Consequential, destructive, or deployment tasks are quarantined in `waiting_approval`.
- Direct API status updates and agent bypasses are blocked with **HTTP 403 Forbidden**.
- Authorizations require authentic reviewer interaction through the dedicated approval endpoints.

### 5. Cybernetic Dashboard
- Built with **React 19, TypeScript, Vite, and Lucide Icons**.
- Interactive DAG visualization, real-time task polling, RAG document search/ingest, deliverable artifact code inspection, and model fleet telemetry.

---

## 🛠️ Project Directory Structure

```
Autonomous-AI-Multi-Agent-Orchestration-Platform/
├── backend/
│   ├── app/
│   │   ├── api/routes/          # REST endpoints (projects, runs, tasks, models, approvals, artifacts, rag)
│   │   ├── core/                # Configuration and environment loaders (CORS, DB, API keys)
│   │   ├── database/            # MongoDB Atlas Async Motor client & compound index managers
│   │   ├── models/              # Pydantic schemas (Project, Run, Task, ModelRegistry, Approval, Artifact)
│   │   ├── services/
│   │   │   ├── model_adapter.py # Hybrid inference adapter (Ollama + Gemini + Offline fallback)
│   │   │   ├── router.py        # ML RandomForest router with data sovereignty guard
│   │   │   ├── orchestrator.py  # DAG scheduler, topological resolver, and checkpoint recovery
│   │   │   ├── embedding_service.py # Embedding generation engine
│   │   │   └── rag_service.py   # RAG ingestion, deduplication, and vector search
│   │   └── main.py              # FastAPI app with lifespan hooks & strict CORS whitelisting
│   ├── tests/
│   │   ├── test_api.py          # Core API lifecycle tests
│   │   ├── test_security_and_rag.py # Consequential gating, bypass blocking, and RAG isolation
│   │   └── test_audit_regressions.py # Checkpoint recovery, duplicate ingestion, CORS, and data sovereignty
│   └── run.py                   # Development server launcher
├── frontend/
│   ├── src/
│   │   ├── components/          # TaskDAGViewer, NewRunModal, ApprovalsDrawer, ArtifactsModal, ModelRegistryPanel
│   │   ├── services/api.ts      # Typed frontend API client
│   │   ├── types/index.ts       # TypeScript contract types
│   │   ├── index.css            # Cybernetic glassmorphism design system
│   │   └── App.tsx              # Primary orchestration dashboard
│   ├── package.json
│   └── vite.config.ts
├── ml/
│   ├── data/                    # Agent task classification datasets
│   ├── models/                  # Serialized ML router models and label encoders
│   ├── router_trainer.py        # ML training and evaluation script
│   └── audit_router.py          # Leakage-resistant holdout audit script
├── agent_prompts/               # System prompt contracts (Planner, Researcher, Developer, Reviewer)
├── docs/
│   ├── ARCHITECTURE.md          # Architectural specification and flowcharts
│   ├── DEPLOYMENT_GUIDE.md      # Production runbook, backup/recovery, and rollback plans
│   └── ML_ROUTER_AUDIT.md       # Full statistical audit report of the ML router
├── Dockerfile                   # Multi-stage production container
├── docker-compose.yml           # Multi-service stack (Backend, Frontend, MongoDB)
├── requirements.txt             # Locked Python dependencies
├── pytest.ini                   # Pytest configuration
├── .env.example                 # Sanitized environment template
└── README.md
```

---

## 🏃 Quick Start Guide

### Option A: Local Development Setup

#### 1. Prerequisites
- **Python 3.11+**
- **Node.js 20+ & npm 10+**
- (Optional) **Ollama** running locally on port `11434`
- (Optional) **MongoDB Atlas** cluster URI

#### 2. Environment Configuration
```bash
cp .env.example .env
# Edit .env with your MONGODB_URI and GEMINI_API_KEY (or leave blank to use resilient fallback mode)
```

#### 3. Backend Setup
```bash
# Windows
.\venv\Scripts\Activate.ps1
# Linux / macOS
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run full test suite (17 passed)
pytest

# Start backend server
python backend/run.py
# API Docs available at http://localhost:8000/docs
```

#### 4. Frontend Dashboard Setup
```bash
cd frontend
npm install
npm run dev
# Dashboard running at http://localhost:5173
```

---

### Option B: Docker Compose Deployment

Run the complete multi-tier platform in isolated containers:

```bash
# Build and start services
docker-compose up --build -d

# Check service logs
docker-compose logs -f backend
```

- **Frontend Dashboard:** `http://localhost:5173`
- **Backend API & Swagger Docs:** `http://localhost:8000/docs`
- **API Health Check:** `http://localhost:8000/health`

---

## 🧪 Testing & Verification

Execute the complete regression and verification test suite:

```bash
pytest backend/tests/ -v
```

### Verified Test Summary (17 Passed)
- `test_health_endpoint`: Health check and system readiness probe.
- `test_project_lifecycle`: Project creation, isolation, and metadata validation.
- `test_model_router_capabilities`: Capability heuristics and model fleet resolution.
- `test_run_and_task_execution`: DAG task scheduling and topological progression.
- `test_cors_origin_whitelisting`: Strict CORS origin validation.
- `test_rag_duplicate_ingestion_prevention`: SHA-256 chunk deduplication idempotency.
- `test_rag_document_and_project_deletion`: Cascading deletion of vector memory.
- `test_project_isolation_in_vector_retrieval`: Cross-tenant RAG search isolation.
- `test_data_sovereignty_guard`: Blocking cloud egress on confidential workloads.
- `test_checkpoint_recovery`: Resumption of DAG runs from interrupted states.
- `test_consequential_action_gating`: Approval queue enforcement for critical operations.
- `test_direct_api_bypass_blocked`: Rejection of unauthorized status updates (HTTP 403).
- `test_legitimate_human_approval_flow`: End-to-end human authorization lifecycle.
- `test_rag_document_ingestion_and_chunking`: Vector chunking and metadata attribution.
- `test_rag_access_control_filtering`: Role and project level filtering.
- `test_real_model_adapter_gemini`: Live adapter interface compatibility.
- `test_model_adapter_fallback_resilience`: Graceful failover to local offline synthesis.

---

## 📊 Machine Learning Model Router Benchmark

Audited against 589 deduplicated real-world agent tasks with 5-fold cross-validation:

| Metric | Score |
| :--- | :--- |
| **Cross-Validation Accuracy** | **99.66% (+/- 0.42%)** |
| **Held-Out Test Accuracy** | **99.32%** |
| **Held-Out Macro F1** | **99.13%** |
| **Data Leakage** | **0.00%** |
| **Rule-Based Baseline Accuracy** | 71.62% |
| **Performance Lift** | **+27.70%** |
| **Cloud Cost Reduction** | **87.8% Savings** |

For the complete statistical breakdown and confusion matrix, see [docs/ML_ROUTER_AUDIT.md](docs/ML_ROUTER_AUDIT.md).

---

## 🛡️ Security & Production Hardening

- **CORS Protection:** Configurable whitelist via `CORS_ORIGINS`; wildcards prohibited.
- **Zero Secrets in VCS:** Strict `.gitignore` policy protecting environment variables, tokens, and keys.
- **Approval Gateway:** Cryptographically tamper-resistant human review loop for consequential tasks.
- **Data Sovereignty:** Dynamic routing prevents enterprise-confidential context from egressing to third-party APIs.
- **Cascading Deletion:** Complete removal of vectors and chunks upon project or document deletion.

---

## 📄 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
