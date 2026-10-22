# Production Deployment & Operational Runbook
**Project:** Autonomous AI Multi-Agent Orchestration Platform  
**Target Environment:** Containerized Cloud / On-Premise Workstation  
**Author:** Ayush Srivastava (AKTU / United College of Engineering & Research, Prayagraj)  
**Date:** October 2026  
**Artifact:** `docs/DEPLOYMENT_GUIDE.md`

---

## 1. Safe Deployment Checklist

Before initiating production deployment, verify all prerequisites:

- [x] **Secrets Hygiene:** `.env` is excluded from git via `.gitignore`. No hardcoded credentials exist in source files.
- [x] **Database Connectivity:** MongoDB Atlas URI verified with read/write credentials and network access whitelist.
- [x] **Compound Indexes Verified:** Compound unique index `[("run_id", 1), ("task_id", 1)]` active on `tasks` collection. Document and embedding indexes active on `documents` and `project_embeddings`.
- [x] **CORS Security:** `allow_origins` strictly whitelisted via `settings.CORS_ORIGINS`; wildcard `*` disabled for credentialed requests.
- [x] **Data Sovereignty Guards:** Confidential workloads automatically blocked from public cloud egress and retained on local Ollama models.
- [x] **Human-in-the-Loop Gatekeeper:** Consequential keywords (`deploy`, `delete`, `drop`, `terminate`, `wipe`, `production_write`) automatically require operator approval. Direct status bypass attempts blocked with `HTTP 403 Forbidden`.
- [x] **Frontend Production Build:** Verified clean with `npm run build` with zero TypeScript or asset compilation errors.
- [x] **Model Endpoint Verification:** Local Ollama fallback tested; Google Gemini 3.5 Flash endpoint live and tested with token budgets.

---

## 2. Docker & Containerized Launch

### Starting the Platform
```bash
# 1. Ensure .env is populated with production keys
cp .env.example .env
# Edit .env with your real MONGODB_URI and GEMINI_API_KEY

# 2. Build and launch containers
docker compose up -d --build

# 3. Verify container health status
docker compose ps
curl http://localhost:8000/health
```

### Pulling Recommended Local LLM Weights
```bash
docker exec -it ollama_runtime ollama pull qwen2.5:latest
docker exec -it ollama_runtime ollama pull deepseek-coder:6.7b
docker exec -it ollama_runtime ollama pull llama3.2:latest
```

---

## 3. Database Backup & Disaster Recovery Plan

### Automated MongoDB Atlas Backups
1. **Continuous Cloud Backups:** Enable Point-In-Time Restore (PITR) in MongoDB Atlas under *Cluster -> Backup*. Retain 7 days of automated hourly snapshots.
2. **Scheduled Local Cold Dumps:**
   ```bash
   mongodump --uri="${MONGODB_URI}" --db=multi_agent_platform --out=/backups/$(date +%Y%m%d_%H%M%S)
   ```

### Recovery Procedure
In the event of database corruption or unintended data loss:
1. Halt background worker processes:
   ```bash
   docker compose stop app
   ```
2. Restore from the most recent known-good backup:
   ```bash
   mongorestore --uri="${MONGODB_URI}" --db=multi_agent_platform --drop /backups/<TARGET_SNAPSHOT>/multi_agent_platform
   ```
3. Verify index integrity:
   ```bash
   python -c "import asyncio; from backend.app.database.mongodb import db_manager; from backend.app.database.indexes import create_indexes; asyncio.run(db_manager.connect()); asyncio.run(create_indexes())"
   ```
4. Restart application container:
   ```bash
   docker compose start app
   ```

---

## 4. Rollback Procedure

If a deployed version exhibits anomalies or fails regression testing in production:

1. **Revert Application Image to Previous Stable Tag:**
   ```bash
   docker compose down
   git checkout tags/v1.0.0-stable
   docker compose up -d --build
   ```
2. **Checkpoint Recovery for In-Flight Runs:**
   Interrupted runs are safely recorded with status `RUNNING`. Use the checkpoint recovery endpoint to resume without re-running completed tasks:
   ```bash
   curl -X POST http://localhost:8000/api/v1/runs/{RUN_ID}/resume
   ```
3. **Verify Zero Data Corruption:**
   Run health check to ensure MongoDB Atlas connection and vector search remain synchronized:
   ```bash
   curl http://localhost:8000/health
   ```

---

## 5. Security & Operational Guardrails

| Guardrail | Enforcement Mechanism | Failure Mode Behavior |
| :--- | :--- | :--- |
| **Destructive Actions** | Pattern-matching engine flags consequential tasks | Task pauses with status `WAITING_APPROVAL`. Direct API bypass returns `403 Forbidden`. |
| **Data Sovereignty** | `_apply_data_sovereignty_guard` in router | Redirects confidential tasks to on-premise Ollama model; blocks network transmission. |
| **Cloud Endpoint Outages** | Resilient 4-tier model adapter fallback | Degrades to local Ollama or deterministic synthesis engine without crashing run. |
| **RAG Duplicate Ingestion** | SHA-256 content hash check | Updates existing document record; replaces chunks to prevent vector index pollution. |
| **Cross-Project Isolation** | Scoped queries by `project_id` across database and vector search | Chunks from Project A are strictly filtered and never surfaced to Project B queries. |
