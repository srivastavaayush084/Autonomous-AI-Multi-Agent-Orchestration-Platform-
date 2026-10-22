from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from app.models.approval import ApprovalRequest, ApprovalDecision
from app.services.orchestrator import orchestrator

router = APIRouter()


@router.get("/", response_model=List[ApprovalRequest])
async def list_approvals(run_id: Optional[str] = Query(None)):
    return await orchestrator.list_approvals(run_id=run_id)


@router.post("/{approval_id}/decide", response_model=ApprovalRequest)
async def decide_approval(approval_id: str, decision_data: ApprovalDecision):
    updated = await orchestrator.process_approval_decision(
        approval_id=approval_id,
        decision=decision_data.decision,
        reason=decision_data.reason or ""
    )
    if not updated:
        raise HTTPException(status_code=400, detail="Approval request not found or already completed")
    return updated
