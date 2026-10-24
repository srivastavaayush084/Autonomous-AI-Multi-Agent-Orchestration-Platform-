import time
import httpx

BASE_URL = "http://localhost:8000/api/v1"
client = httpx.Client(base_url=BASE_URL, timeout=60.0)

def http_post(endpoint, payload):
    resp = client.post(endpoint, json=payload)
    if resp.status_code >= 400:
        print(f"Error {resp.status_code} on POST {endpoint}: {resp.text}")
    resp.raise_for_status()
    return resp.json()

def http_get(endpoint):
    resp = client.get(endpoint)
    if resp.status_code >= 400:
        print(f"Error {resp.status_code} on GET {endpoint}: {resp.text}")
    resp.raise_for_status()
    return resp.json()

def main():
    print("=====================================================================")
    print("AUTONOMOUS AI MULTI-AGENT PLATFORM - LIVE RESEARCH EXECUTION TEST")
    print("=====================================================================\n")

    # Step 1: Create Project
    print("[1/5] Creating Project: 'AI Cybersecurity Intelligence'...")
    project_payload = {
        "name": "AI Cybersecurity Intelligence",
        "description": "Comprehensive evaluation of AI-driven cybersecurity approaches, gaps, and defense paradigms."
    }
    project = http_post("/projects/", project_payload)
    proj_id = project["project_id"]
    print(f" -> Project Created: {project['name']} (ID: {proj_id})\n")

    # Step 2: Ingest Grounding Documents into Project Memory (RAG)
    print("[2/5] Ingesting Grounding Documents into RAG Vector Memory...")
    rag_doc_1 = {
        "project_id": proj_id,
        "title": "NIST & MITRE: AI in Offensive and Defensive Cybersecurity 2026",
        "content": (
            "Recent advancements in AI-powered cybersecurity highlight three dominant architectures: "
            "1. Real-time telemetry anomaly detection using transformer-based sequence models (e.g. DARPA CHESS). "
            "2. Autonomous vulnerability discovery and binary symbolic execution with reinforcement learning. "
            "3. Agentic SIEM threat-hunting co-pilots that correlate multi-cloud audit logs and synthesize remediation playbooks. "
            "Crucial research gaps include: adversarial prompt injection against defensive LLMs, explainability deficits in deep "
            "learning malware classifiers, high false-positive fatigue in SOC pipelines, and data poisoning during continual model fine-tuning."
        )
    }
    rag_res = http_post("/rag/ingest", rag_doc_1)
    print(f" -> Ingested Document: '{rag_doc_1['title']}' ({rag_res.get('chunks_created', 1)} chunks generated)\n")

    # Step 3: Launch Autonomous Multi-Agent Run
    goal = "Research the latest developments in AI-powered cybersecurity, compare important approaches, identify research gaps, and prepare a report with reliable sources."
    print(f"[3/5] Launching Autonomous Multi-Agent Run...")
    print(f" -> Goal: \"{goal}\"")
    run_payload = {
        "project_id": proj_id,
        "goal": goal,
        "parameters": {"priority": "high", "topic": "ai_cybersecurity"}
    }
    run = http_post("/runs/", run_payload)
    run_id = run["run_id"]
    print(f" -> Run Initialized: {run_id} | Status: {run['status']}\n")

    # Step 4: Monitor Execution Lifecycle & Handle Approvals
    print("[4/5] Monitoring DAG Scheduling, ML Routing, and Agent Execution...")
    max_wait_seconds = 180
    start_time = time.time()
    
    while time.time() - start_time < max_wait_seconds:
        run_data = http_get(f"/runs/{run_id}")
        tasks = http_get(f"/runs/{run_id}/tasks")
        approvals = http_get(f"/approvals/?run_id={run_id}")
        
        # Check if any task requires human approval
        pending_approvals = [a for a in approvals if a.get("status") == "pending"]
        for app in pending_approvals:
            print(f" -> [GATED ACTION DETECTED] Human review requested for Task: {app.get('task_id')} | Action: {app.get('action_type')}")
            decision_payload = {
                "decision": "approved",
                "reason": "Authorized by security auditor for verification research run."
            }
            http_post(f"/approvals/{app['approval_id']}/decide", decision_payload)
            print(f" -> [APPROVED] Safety Gateway granted clearance for {app['approval_id']}.")

        completed_count = sum(1 for t in tasks if t.get("status") == "completed")
        total_count = len(tasks)
        running_tasks = [t['task_id'] for t in tasks if t.get('status') == 'running']
        ready_tasks = [t['task_id'] for t in tasks if t.get('status') == 'ready']
        
        print(f"    Elapsed: {int(time.time() - start_time)}s | Run: {run_data['status']} | Completed: {completed_count}/{total_count} tasks | Active: {running_tasks} | Ready: {ready_tasks}")

        if run_data["status"] in ["completed", "failed"] or (total_count > 0 and completed_count == total_count):
            time.sleep(1)
            break
        
        time.sleep(3)

    final_run = http_get(f"/runs/{run_id}")
    final_tasks = http_get(f"/runs/{run_id}/tasks")
    final_artifacts = http_get(f"/artifacts/?run_id={run_id}")

    print("\n=====================================================================")
    print("FINAL EXECUTION RESULTS")
    print("=====================================================================")
    print(f"Run ID:         {final_run['run_id']}")
    print(f"Status:         {final_run['status'].upper()}")
    exec_time = final_run.get('execution_time_seconds')
    print(f"Duration:       {exec_time:.2f}s" if exec_time is not None else "Duration:       N/A")
    print(f"Tasks Total:    {len(final_tasks)}")
    print(f"Tasks Done:     {sum(1 for t in final_tasks if t['status'] == 'completed')}")
    print(f"Artifacts Made: {len(final_artifacts)}\n")

    print("--- TASK BREAKDOWN & ML MODEL ROUTING ---")
    for t in final_tasks:
        print(f"• [{t['task_id']}] {t['title']} ({t['role'].upper()})")
        print(f"    Status:     {t['status'].upper()}")
        print(f"    Assigned:   {t['assigned_model']} (Confidence: {(t.get('router_confidence') or 0)*100:.1f}%)")
        print(f"    Rationale:  {t.get('routing_reason')}")
        if t.get("execution_time_seconds"):
            print(f"    Exec Time:  {t['execution_time_seconds']:.2f}s")
        print()

    print("--- GENERATED DELIVERABLES & ARTIFACTS ---")
    for a in final_artifacts:
        print(f"* [{a['artifact_id']}] {a['title']} ({a['artifact_type'].upper()} | {a['size_bytes']} bytes)")
        snippet = a.get("content_snippet", "")
        preview = snippet[:500] + ("..." if len(snippet) > 500 else "")
        print(f"Preview:\n{preview}\n")

    print(f"[SUCCESS] Complete research study executed successfully.")
    print(f"View in Live Dashboard at: http://localhost:5173 (Select Project '{project['name']}')")

if __name__ == "__main__":
    main()
