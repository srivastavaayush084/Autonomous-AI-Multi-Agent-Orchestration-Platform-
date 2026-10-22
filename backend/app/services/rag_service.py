import logging
import uuid
import hashlib
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from app.database.mongodb import db_manager
from app.models.rag import (
    DocumentIngestRequest,
    DocumentChunk,
    RAGSearchResult,
    RAGQueryResponse
)
from app.services.embedding_service import embedding_service

logger = logging.getLogger(__name__)


class RAGService:
    def __init__(self):
        # In-memory vector store mirror for dual-mode / offline resilience
        self.mem_chunks: List[Dict[str, Any]] = []
        self.mem_docs: Dict[str, Dict[str, Any]] = {}

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def _chunk_text(self, text: str, chunk_size: int = 250, overlap: int = 40) -> List[str]:
        words = text.split()
        if len(words) <= chunk_size:
            return [" ".join(words)]

        chunks = []
        start = 0
        while start < len(words):
            end = min(start + chunk_size, len(words))
            chunk_words = words[start:end]
            chunks.append(" ".join(chunk_words))
            if end >= len(words):
                break
            start += (chunk_size - overlap)
        return chunks

    async def ingest_document(self, req: DocumentIngestRequest) -> Dict[str, Any]:
        content_hash = hashlib.sha256(req.content.strip().encode("utf-8")).hexdigest()
        
        # Check if an identical document or same-titled document already exists in this project
        existing_doc_id = None
        for d_id, doc in self.mem_docs.items():
            if doc.get("project_id") == req.project_id and (doc.get("content_hash") == content_hash or doc.get("title") == req.title):
                existing_doc_id = d_id
                break

        if not existing_doc_id and db_manager.connected and db_manager.db is not None:
            try:
                found = await db_manager.db.documents.find_one({
                    "project_id": req.project_id,
                    "$or": [{"content_hash": content_hash}, {"title": req.title}]
                })
                if found:
                    existing_doc_id = found["document_id"]
            except Exception:
                pass

        if existing_doc_id:
            # Cleanly replace prior chunks to prevent duplicate vector explosion
            await self.delete_document(req.project_id, existing_doc_id)
            doc_id = existing_doc_id
        else:
            doc_id = f"doc-{uuid.uuid4().hex[:8]}"

        created_at = self._now()

        # Chunk the content
        text_chunks = self._chunk_text(req.content)
        chunk_docs = []

        for idx, chunk_text in enumerate(text_chunks):
            chunk_id = f"{doc_id}-c{idx+1}"
            vector = await embedding_service.get_embedding(chunk_text)

            chunk_obj = {
                "chunk_id": chunk_id,
                "document_id": doc_id,
                "project_id": req.project_id,
                "title": req.title,
                "chunk_index": idx + 1,
                "text": chunk_text,
                "vector": vector,
                "source_uri": req.source_uri or "local://manual",
                "document_type": req.document_type,
                "allowed_roles": req.allowed_roles,
                "visibility": req.visibility,
                "token_count": len(chunk_text.split()),
                "created_at": created_at,
                "metadata": req.metadata
            }
            chunk_docs.append(chunk_obj)
            self.mem_chunks.append(chunk_obj)

        doc_record = {
            "document_id": doc_id,
            "project_id": req.project_id,
            "title": req.title,
            "content_hash": content_hash,
            "source_uri": req.source_uri,
            "document_type": req.document_type,
            "visibility": req.visibility,
            "allowed_roles": req.allowed_roles,
            "total_chunks": len(chunk_docs),
            "created_at": created_at,
            "metadata": req.metadata
        }
        self.mem_docs[doc_id] = doc_record

        # Persist to MongoDB Atlas if connected
        if db_manager.connected and db_manager.db is not None:
            try:
                await db_manager.db.documents.update_one(
                    {"project_id": req.project_id, "document_id": doc_id},
                    {"$set": doc_record.copy()},
                    upsert=True
                )
                if chunk_docs:
                    await db_manager.db.project_embeddings.insert_many([c.copy() for c in chunk_docs])
                logger.info(f"Ingested document {doc_id} with {len(chunk_docs)} chunks into MongoDB Atlas.")
            except Exception as e:
                logger.error(f"Failed to persist RAG document to MongoDB Atlas: {e}")

        return {
            "document_id": doc_id,
            "title": req.title,
            "chunks_created": len(chunk_docs),
            "project_id": req.project_id,
            "status": "ingested"
        }

    async def search_memory(
        self,
        project_id: str,
        query: str,
        role: str = "researcher",
        top_k: int = 3,
        min_similarity: float = 0.35
    ) -> RAGQueryResponse:
        query_vector = await embedding_service.get_embedding(query)

        # Retrieve candidate chunks (from Atlas if connected, or memory)
        candidate_chunks = []
        if db_manager.connected and db_manager.db is not None:
            try:
                cursor = db_manager.db.project_embeddings.find({"project_id": project_id})
                candidate_chunks = await cursor.to_list(length=1000)
            except Exception as e:
                logger.warning(f"Atlas retrieval failed: {e}. Falling back to memory.")
                candidate_chunks = [c for c in self.mem_chunks if c.get("project_id") == project_id]
        else:
            candidate_chunks = [c for c in self.mem_chunks if c.get("project_id") == project_id]

        scored_results: List[RAGSearchResult] = []

        for chunk in candidate_chunks:
            # 1. Access Control: Role Verification
            allowed_roles = chunk.get("allowed_roles", [])
            if allowed_roles and role not in allowed_roles:
                continue

            # 2. Access Control: Confidentiality Guard
            if chunk.get("visibility") == "confidential" and role not in ["reviewer", "planner"]:
                continue

            # 3. Vector Similarity
            chunk_vec = chunk.get("vector")
            if not chunk_vec:
                continue

            score = embedding_service.cosine_similarity(query_vector, chunk_vec)
            if score >= min_similarity:
                scored_results.append(
                    RAGSearchResult(
                        chunk_id=chunk["chunk_id"],
                        document_id=chunk["document_id"],
                        title=chunk["title"],
                        text=chunk["text"],
                        score=round(score, 4),
                        source_uri=chunk.get("source_uri", ""),
                        chunk_index=chunk.get("chunk_index", 1),
                        visibility=chunk.get("visibility", "internal")
                    )
                )

        # Sort descending by similarity score
        scored_results.sort(key=lambda x: x.score, reverse=True)
        top_results = scored_results[:top_k]

        # Generate source-grounded citation header
        if top_results:
            citations = []
            for r in top_results:
                citations.append(f"[Source: {r.title} (Chunk #{r.chunk_index}) | Match: {r.score*100:.1f}% | Ref: {r.source_uri}]")
            citation_header = "VERIFIED PROJECT MEMORY CONTEXT:\n" + "\n".join(citations) + "\n"
        else:
            citation_header = "NO RELEVANT PROJECT CONTEXT FOUND IN MEMORY."

        return RAGQueryResponse(
            query=query,
            project_id=project_id,
            results=top_results,
            total_found=len(scored_results),
            citation_header=citation_header
        )

    async def list_project_documents(self, project_id: str) -> List[Dict[str, Any]]:
        if db_manager.connected and db_manager.db is not None:
            try:
                cursor = db_manager.db.documents.find({"project_id": project_id}, {"_id": 0}).sort("created_at", -1)
                return await cursor.to_list(length=100)
            except Exception:
                pass
        return [d for d in self.mem_docs.values() if d.get("project_id") == project_id]

    async def delete_document(self, project_id: str, document_id: str) -> bool:
        """Deletes a document and all associated embedding vectors for a project."""
        # 1. Memory mirror cleanup
        self.mem_docs.pop(document_id, None)
        self.mem_chunks = [c for c in self.mem_chunks if not (c.get("document_id") == document_id and c.get("project_id") == project_id)]

        # 2. Database cleanup
        if db_manager.connected and db_manager.db is not None:
            try:
                await db_manager.db.documents.delete_one({"project_id": project_id, "document_id": document_id})
                await db_manager.db.project_embeddings.delete_many({"project_id": project_id, "document_id": document_id})
                logger.info(f"Deleted document {document_id} and its embeddings for project {project_id}.")
                return True
            except Exception as e:
                logger.error(f"Failed to delete document {document_id} from MongoDB: {e}")
                return False
        return True

    async def delete_project_documents(self, project_id: str) -> int:
        """Purges all memory embeddings and document records for a given project."""
        deleted_count = len([d for d in self.mem_docs.values() if d.get("project_id") == project_id])
        self.mem_docs = {k: v for k, v in self.mem_docs.items() if v.get("project_id") != project_id}
        self.mem_chunks = [c for c in self.mem_chunks if c.get("project_id") != project_id]

        if db_manager.connected and db_manager.db is not None:
            try:
                await db_manager.db.documents.delete_many({"project_id": project_id})
                await db_manager.db.project_embeddings.delete_many({"project_id": project_id})
                logger.info(f"Purged all RAG documents and embeddings for project {project_id}.")
            except Exception as e:
                logger.error(f"Failed to purge project RAG data from MongoDB: {e}")
        return deleted_count


rag_service = RAGService()
