from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from app.models.rag import DocumentIngestRequest, RAGQueryRequest, RAGQueryResponse
from app.services.rag_service import rag_service

router = APIRouter()


@router.post("/ingest", status_code=201)
async def ingest_document(data: DocumentIngestRequest):
    return await rag_service.ingest_document(data)


@router.post("/query", response_model=RAGQueryResponse)
async def query_memory(data: RAGQueryRequest):
    return await rag_service.search_memory(
        project_id=data.project_id,
        query=data.query,
        role=data.role or "researcher",
        top_k=data.top_k,
        min_similarity=data.min_similarity
    )


@router.get("/documents/{project_id}")
async def list_documents(project_id: str):
    return await rag_service.list_project_documents(project_id)


@router.delete("/documents/{project_id}/{document_id}")
async def delete_document(project_id: str, document_id: str):
    deleted = await rag_service.delete_document(project_id, document_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found or could not be deleted")
    return {"status": "deleted", "document_id": document_id, "project_id": project_id}
