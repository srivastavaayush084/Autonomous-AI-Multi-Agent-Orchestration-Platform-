import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from app.core.config import settings
from app.database.mongodb import db_manager
from app.models.approval import ApprovalStatus, ApprovalRequest, RiskLevel
from app.models.artifact import ArtifactResponse, ArtifactType
from app.models.run import RunStatus
from app.models.task import TaskStatus
from app.services.model_adapter import model_adapter
from app.services.router import model_router
from app.services.rag_service import rag_service

logger = logging.getLogger(__name__)


class OrchestrationService:
    def __init__(self):
        # In-memory stores used when MongoDB is not connected or in local development mode
        self.mem_projects: Dict[str, Dict[str, Any]] = {}
        self.mem_runs: Dict[str, Dict[str, Any]] = {}
        self.mem_tasks: Dict[str, Dict[str, Any]] = {}
        self.mem_approvals: Dict[str, Dict[str, Any]] = {}
        self.mem_artifacts: Dict[str, Dict[str, Any]] = {}
        self._active_loops: set = set()

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    # ==========================================
    # Project Operations
    # ==========================================
    async def create_project(self, name: str, description: str = "", metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        project_id = f"proj-{uuid.uuid4().hex[:8]}"
        doc = {
            "project_id": project_id,
            "name": name,
            "description": description,
            "created_at": self._now(),
            "updated_at": self._now(),
            "metadata": metadata or {}
        }
        if db_manager.connected and db_manager.db is not None:
            await db_manager.db.projects.insert_one(doc.copy())
        self.mem_projects[project_id] = doc
        return doc

    async def list_projects(self) -> List[Dict[str, Any]]:
        if db_manager.connected and db_manager.db is not None:
            cursor = db_manager.db.projects.find({}, {"_id": 0}).sort("created_at", -1)
            return await cursor.to_list(length=100)
        return list(self.mem_projects.values())

    async def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        if db_manager.connected and db_manager.db is not None:
            doc = await db_manager.db.projects.find_one({"project_id": project_id}, {"_id": 0})
            if doc:
                return doc
        return self.mem_projects.get(project_id)

    async def delete_project(self, project_id: str) -> bool:
        """Cascades deletion of a project, its runs, tasks, approvals, deliverables, and RAG memory."""
        proj = await self.get_project(project_id)
        if not proj:
            return False

        # 1. Memory mirror cleanup
        self.mem_projects.pop(project_id, None)
        project_run_ids = [r["run_id"] for r in self.mem_runs.values() if r.get("project_id") == project_id]
        for r_id in project_run_ids:
            self.mem_runs.pop(r_id, None)
            self.mem_tasks = {k: v for k, v in self.mem_tasks.items() if v.get("run_id") != r_id}
            self.mem_approvals = {k: v for k, v in self.mem_approvals.items() if v.get("run_id") != r_id}
            self.mem_artifacts = {k: v for k, v in self.mem_artifacts.items() if v.get("run_id") != r_id}

        # 2. Database cascade cleanup
        if db_manager.connected and db_manager.db is not None:
            try:
                await db_manager.db.projects.delete_one({"project_id": project_id})
                await db_manager.db.runs.delete_many({"project_id": project_id})
                for r_id in project_run_ids:
                    await db_manager.db.tasks.delete_many({"run_id": r_id})
                    await db_manager.db.approvals.delete_many({"run_id": r_id})
                    await db_manager.db.artifacts.delete_many({"run_id": r_id})
            except Exception as e:
                logger.error(f"Failed to cascade delete project {project_id}: {e}")

        # 3. Purge RAG documents and vector embeddings
        await rag_service.delete_project_documents(project_id)
        logger.info(f"Project {project_id} and all cascaded artifacts successfully deleted.")
        return True

    # ==========================================
    # Run Lifecycle Operations
    # ==========================================
    async def create_run(self, project_id: str, goal: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        run_id = f"run-{uuid.uuid4().hex[:8]}"
        doc = {
            "run_id": run_id,
            "project_id": project_id,
            "goal": goal,
            "status": RunStatus.PENDING,
            "created_at": self._now(),
            "updated_at": self._now(),
            "started_at": None,
            "completed_at": None,
            "execution_time_seconds": None,
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "pending_approvals": 0,
            "error_message": None,
            "metadata": parameters or {}
        }
        if db_manager.connected and db_manager.db is not None:
            await db_manager.db.runs.insert_one(doc.copy())
        self.mem_runs[run_id] = doc

        # Trigger background orchestration
        asyncio.create_task(self.start_run_execution(run_id))
        return doc

    async def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        if db_manager.connected and db_manager.db is not None:
            doc = await db_manager.db.runs.find_one({"run_id": run_id}, {"_id": 0})
            if doc:
                return doc
        return self.mem_runs.get(run_id)

    async def list_runs(self, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if db_manager.connected and db_manager.db is not None:
            q = {"project_id": project_id} if project_id else {}
            cursor = db_manager.db.runs.find(q, {"_id": 0}).sort("created_at", -1)
            return await cursor.to_list(length=100)
        
        runs = list(self.mem_runs.values())
        if project_id:
            runs = [r for r in runs if r.get("project_id") == project_id]
        return sorted(runs, key=lambda x: x["created_at"], reverse=True)

    async def resume_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Checkpoint recovery: Resumes an interrupted run from its last completed state."""
        run = await self.get_run(run_id)
        if not run:
            return None

        tasks = await self.get_run_tasks(run_id)
        for t in tasks:
            if t["status"] == TaskStatus.RUNNING:
                t["status"] = TaskStatus.PENDING
                await self._save_task(t)

        run["status"] = RunStatus.RUNNING
        await self._save_run(run)

        # Relaunch the execution DAG loop asynchronously
        asyncio.create_task(self._execute_dag_loop(run_id))
        return run

    # ==========================================
    # Autonomous Multi-Agent Execution Engine
    # ==========================================
    async def start_run_execution(self, run_id: str):
        run = await self.get_run(run_id)
        if not run:
            return

        run["status"] = RunStatus.PLANNING
        run["started_at"] = self._now()
        await self._save_run(run)

        # 1. Planner Agent Decomposition
        planner_system = (
            "You are the Master Planner Agent. Decompose the goal into structured subtasks with dependencies and acceptance criteria."
        )
        planner_prompt = f"Decompose this project goal into an execution DAG:\n{run['goal']}"

        try:
            raw_plan = await model_adapter.generate("ollama/qwen2.5:latest", planner_system, planner_prompt)
            plan_json = json.loads(raw_plan)
            tasks_data = plan_json.get("tasks", [])
        except Exception as e:
            logger.error(f"Planning failed: {e}. Generating default DAG.")
            tasks_data = [
                {
                    "task_id": "T1-research",
                    "title": "Technical Requirements & Context",
                    "role": "researcher",
                    "goal": f"Gather context for: {run['goal']}",
                    "depends_on": [],
                    "acceptance_criteria": ["Document constraints"],
                    "requires_approval": False,
                    "estimated_complexity": "low"
                },
                {
                    "task_id": "T2-dev",
                    "title": "Implementation Module",
                    "role": "developer",
                    "goal": "Develop software deliverable",
                    "depends_on": ["T1-research"],
                    "acceptance_criteria": ["All tests pass"],
                    "requires_approval": False,
                    "estimated_complexity": "medium"
                },
                {
                    "task_id": "T3-qa",
                    "title": "Quality Verification",
                    "role": "reviewer",
                    "goal": "Audit outputs",
                    "depends_on": ["T2-dev"],
                    "acceptance_criteria": ["Criteria verified"],
                    "requires_approval": False,
                    "estimated_complexity": "low"
                }
            ]

        # 2. Persist Tasks and Route Models
        for t in tasks_data:
            assigned_model, routing_reason, confidence = model_router.route_task(t)
            
            # Security Guard: Consequential actions strictly enforce human approval
            consequential_keywords = ["deploy", "delete", "drop", "terminate", "wipe", "production_write", "charge", "external_publish"]
            is_consequential = any(k in t.get("title", "").lower() or k in t.get("goal", "").lower() for k in consequential_keywords)
            enforced_approval = t.get("requires_approval", False) or is_consequential

            task_doc = {
                "task_id": t["task_id"],
                "run_id": run_id,
                "title": t["title"],
                "role": t["role"],
                "goal": t["goal"],
                "status": TaskStatus.PENDING,
                "depends_on": t.get("depends_on", []),
                "acceptance_criteria": t.get("acceptance_criteria", []),
                "requires_approval": enforced_approval,
                "assigned_model": assigned_model,
                "routing_reason": routing_reason,
                "router_confidence": confidence,
                "attempts": 0,
                "max_attempts": 3,
                "result_summary": None,
                "output_data": None,
                "error_message": None,
                "started_at": None,
                "completed_at": None,
                "execution_time_seconds": None,
                "created_at": self._now(),
                "updated_at": self._now()
            }
            await self._save_task(task_doc)

        run["total_tasks"] = len(tasks_data)
        run["status"] = RunStatus.RUNNING
        await self._save_run(run)

        # 3. Continuous DAG Execution Loop
        await self._execute_dag_loop(run_id)

    async def _execute_dag_loop(self, run_id: str):
        if run_id in self._active_loops:
            logger.info(f"DAG loop for run {run_id} is already active.")
            return
        self._active_loops.add(run_id)

        try:
            while True:
                run = await self.get_run(run_id)
                if not run or run["status"] in [RunStatus.COMPLETED, RunStatus.FAILED, RunStatus.CANCELLED]:
                    break

                tasks = await self.get_run_tasks(run_id)
                completed_ids = {t["task_id"] for t in tasks if t["status"] == TaskStatus.COMPLETED}
                failed_tasks = [t for t in tasks if t["status"] == TaskStatus.FAILED]
                
                if failed_tasks:
                    run["status"] = RunStatus.FAILED
                    run["error_message"] = f"Task {failed_tasks[0]['task_id']} failed after maximum attempts."
                    run["completed_at"] = self._now()
                    await self._save_run(run)
                    break

                # Find tasks that are ready to run (dependencies completed and currently pending or ready)
                ready_tasks = [
                    t for t in tasks 
                    if t["status"] in [TaskStatus.PENDING, TaskStatus.READY] and all(dep in completed_ids for dep in t["depends_on"])
                ]

                if not ready_tasks:
                    # Check if all tasks completed
                    if len(completed_ids) == len(tasks) and len(tasks) > 0:
                        run["status"] = RunStatus.COMPLETED
                        run["completed_at"] = self._now()
                        if run["started_at"]:
                            run["execution_time_seconds"] = (run["completed_at"] - run["started_at"]).total_seconds()
                        run["completed_tasks"] = len(completed_ids)
                        await self._save_run(run)
                    break

                # Execute ready tasks in parallel
                await asyncio.gather(*[self._execute_single_task(t) for t in ready_tasks])
                await asyncio.sleep(0.5)
        finally:
            self._active_loops.discard(run_id)

    async def _execute_single_task(self, task: Dict[str, Any]):
        run_id = task["run_id"]
        task_id = task["task_id"]

        # Check for Human-In-The-Loop Approval requirement
        if task.get("requires_approval", False) and task["status"] != TaskStatus.READY:
            task["status"] = TaskStatus.WAITING_APPROVAL
            await self._save_task(task)
            
            # Create Approval Request record
            approval_doc = {
                "approval_id": f"appr-{uuid.uuid4().hex[:8]}",
                "run_id": run_id,
                "task_id": task_id,
                "action_type": "deploy_action" if "deploy" in task["title"].lower() else "external_action",
                "description": f"Human authorization requested for task: {task['title']} ({task['goal']})",
                "risk_level": RiskLevel.HIGH if "deploy" in task["title"].lower() else RiskLevel.MEDIUM,
                "status": ApprovalStatus.PENDING,
                "payload": {"goal": task["goal"], "acceptance_criteria": task["acceptance_criteria"]},
                "created_at": self._now(),
                "decided_at": None,
                "decided_by": None,
                "decision_reason": None
            }
            await self._save_approval(approval_doc)
            
            run = await self.get_run(run_id)
            if run:
                run["status"] = RunStatus.WAITING_APPROVAL
                run["pending_approvals"] = run.get("pending_approvals", 0) + 1
                await self._save_run(run)
            return

        # Execute task worker
        task["status"] = TaskStatus.RUNNING
        task["started_at"] = self._now()
        task["attempts"] = task.get("attempts", 0) + 1
        await self._save_task(task)

        start_time = self._now()
        assigned_model = task.get("assigned_model", "ollama/qwen2.5:latest")
        system_prompt = f"You are a specialized {task['role']} agent. Complete the task thoroughly with strict factual grounding."

        # Query Project Memory (RAG) for source-grounded context
        run = await self.get_run(run_id)
        project_id = run.get("project_id", "default") if run else "default"
        rag_res = await rag_service.search_memory(project_id, task["goal"], role=task["role"], top_k=3)
        rag_context = f"\n{rag_res.citation_header}\n" if rag_res.results else ""

        user_prompt = f"{rag_context}Goal: {task['goal']}\nAcceptance Criteria: {', '.join(task['acceptance_criteria'])}"

        try:
            # Model execution
            response_text = await model_adapter.generate(assigned_model, system_prompt, user_prompt)
            duration = (self._now() - start_time).total_seconds()
            
            task["status"] = TaskStatus.COMPLETED
            task["completed_at"] = self._now()
            task["execution_time_seconds"] = duration
            task["result_summary"] = f"Successfully generated deliverable for {task['title']}."
            
            try:
                task["output_data"] = json.loads(response_text)
            except Exception:
                task["output_data"] = {"text": response_text}

            await self._save_task(task)

            # Register artifact with citation metadata
            artifact_id = f"art-{uuid.uuid4().hex[:8]}"
            artifact_doc = {
                "artifact_id": artifact_id,
                "run_id": run_id,
                "task_id": task_id,
                "title": f"Deliverable - {task['title']}",
                "artifact_type": ArtifactType.REPORT if task["role"] == "researcher" else ArtifactType.CODE,
                "content_snippet": response_text[:300],
                "size_bytes": len(response_text.encode('utf-8')),
                "created_at": self._now(),
                "metadata": {
                    "model": assigned_model,
                    "role": task["role"],
                    "sources_cited": [r.title for r in rag_res.results] if rag_res.results else []
                }
            }
            await self._save_artifact(artifact_doc)

            # Update run stats
            run = await self.get_run(run_id)
            if run:
                run["completed_tasks"] = run.get("completed_tasks", 0) + 1
                await self._save_run(run)

        except Exception as e:
            logger.error(f"Task {task_id} execution error: {e}")
            if task["attempts"] < task.get("max_attempts", 3):
                task["status"] = TaskStatus.PENDING  # Retry
            else:
                task["status"] = TaskStatus.FAILED
                task["error_message"] = str(e)
            await self._save_task(task)

    # ==========================================
    # Approval Decisions
    # ==========================================
    async def process_approval_decision(self, approval_id: str, decision: ApprovalStatus, reason: str = "") -> Optional[Dict[str, Any]]:
        approval = await self.get_approval(approval_id)
        if not approval or approval["status"] != ApprovalStatus.PENDING:
            return None

        approval["status"] = decision
        approval["decided_at"] = self._now()
        approval["decided_by"] = "human_operator"
        approval["decision_reason"] = reason
        await self._save_approval(approval)

        task = await self.get_task(approval["task_id"])
        run = await self.get_run(approval["run_id"])

        if run and run.get("pending_approvals", 0) > 0:
            run["pending_approvals"] -= 1

        if decision == ApprovalStatus.APPROVED:
            if task:
                task["status"] = TaskStatus.READY
                task["requires_approval"] = False
                await self._save_task(task)
            if run and run["status"] == RunStatus.WAITING_APPROVAL and run.get("pending_approvals", 0) == 0:
                run["status"] = RunStatus.RUNNING
                await self._save_run(run)
            
            # Resume DAG execution
            asyncio.create_task(self._execute_dag_loop(approval["run_id"]))
        else:
            if task:
                task["status"] = TaskStatus.FAILED
                task["error_message"] = f"Action rejected by human reviewer: {reason}"
                await self._save_task(task)
            if run:
                run["status"] = RunStatus.FAILED
                run["error_message"] = f"Run stopped due to rejected approval on task {task['title']}."
                await self._save_run(run)

        return approval

    # ==========================================
    # Getters & Persistence Helpers
    # ==========================================
    async def get_run_tasks(self, run_id: str) -> List[Dict[str, Any]]:
        if db_manager.connected and db_manager.db is not None:
            cursor = db_manager.db.tasks.find({"run_id": run_id}, {"_id": 0})
            return await cursor.to_list(length=100)
        return [t for t in self.mem_tasks.values() if t.get("run_id") == run_id]

    async def get_task(self, task_id: str, run_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        if db_manager.connected and db_manager.db is not None:
            q = {"task_id": task_id}
            if run_id:
                q["run_id"] = run_id
            return await db_manager.db.tasks.find_one(q, {"_id": 0})
        if run_id:
            return self.mem_tasks.get(f"{run_id}_{task_id}")
        for t in reversed(list(self.mem_tasks.values())):
            if t.get("task_id") == task_id:
                return t
        return None

    async def update_task_status_safe(self, task_id: str, new_status: TaskStatus, run_id: Optional[str] = None) -> Dict[str, Any]:
        task = await self.get_task(task_id, run_id=run_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        # Security Enforcement: Check if task was gated by human approval
        if task.get("requires_approval", False) and new_status in [TaskStatus.COMPLETED, TaskStatus.RUNNING]:
            approvals = await self.list_approvals(run_id=task.get("run_id"))
            task_approvals = [a for a in approvals if a.get("task_id") == task_id]
            is_approved = any(a.get("status") == ApprovalStatus.APPROVED for a in task_approvals)
            if not is_approved:
                logger.warning(f"Security Alert: Attempted unauthorized status transition to '{new_status}' on gated task {task_id}.")
                raise PermissionError("Security Policy Violation: Consequential task requires authorized human operator approval and cannot be bypassed.")

        task["status"] = new_status
        await self._save_task(task)
        return task

    async def get_approval(self, approval_id: str) -> Optional[Dict[str, Any]]:
        if db_manager.connected and db_manager.db is not None:
            return await db_manager.db.approvals.find_one({"approval_id": approval_id}, {"_id": 0})
        return self.mem_approvals.get(approval_id)

    async def list_approvals(self, run_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if db_manager.connected and db_manager.db is not None:
            q = {"run_id": run_id} if run_id else {}
            cursor = db_manager.db.approvals.find(q, {"_id": 0}).sort("created_at", -1)
            return await cursor.to_list(length=100)
        items = list(self.mem_approvals.values())
        if run_id:
            items = [a for a in items if a.get("run_id") == run_id]
        return sorted(items, key=lambda x: x["created_at"], reverse=True)

    async def list_artifacts(self, run_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if db_manager.connected and db_manager.db is not None:
            q = {"run_id": run_id} if run_id else {}
            cursor = db_manager.db.artifacts.find(q, {"_id": 0}).sort("created_at", -1)
            return await cursor.to_list(length=100)
        items = list(self.mem_artifacts.values())
        if run_id:
            items = [a for a in items if a.get("run_id") == run_id]
        return sorted(items, key=lambda x: x["created_at"], reverse=True)

    async def _save_run(self, run: Dict[str, Any]):
        run["updated_at"] = self._now()
        self.mem_runs[run["run_id"]] = run
        if db_manager.connected and db_manager.db is not None:
            await db_manager.db.runs.update_one(
                {"run_id": run["run_id"]},
                {"$set": run},
                upsert=True
            )

    async def _save_task(self, task: Dict[str, Any]):
        task["updated_at"] = self._now()
        task_key = f"{task['run_id']}_{task['task_id']}"
        self.mem_tasks[task_key] = task
        if db_manager.connected and db_manager.db is not None:
            await db_manager.db.tasks.update_one(
                {"run_id": task["run_id"], "task_id": task["task_id"]},
                {"$set": task},
                upsert=True
            )

    async def _save_approval(self, approval: Dict[str, Any]):
        self.mem_approvals[approval["approval_id"]] = approval
        if db_manager.connected and db_manager.db is not None:
            await db_manager.db.approvals.update_one(
                {"approval_id": approval["approval_id"]},
                {"$set": approval},
                upsert=True
            )

    async def _save_artifact(self, artifact: Dict[str, Any]):
        self.mem_artifacts[artifact["artifact_id"]] = artifact
        if db_manager.connected and db_manager.db is not None:
            await db_manager.db.artifacts.update_one(
                {"artifact_id": artifact["artifact_id"]},
                {"$set": artifact},
                upsert=True
            )


orchestrator = OrchestrationService()
