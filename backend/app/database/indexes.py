import logging
from app.database.mongodb import db_manager

logger = logging.getLogger(__name__)


async def create_indexes():
    if not db_manager.connected or db_manager.db is None:
        logger.info("Skipping MongoDB index creation: Database not connected.")
        return

    db = db_manager.db
    try:
        # Projects indexes
        await db.projects.create_index("project_id", unique=True)
        await db.projects.create_index("created_at")

        # Runs indexes
        await db.runs.create_index("run_id", unique=True)
        await db.runs.create_index("project_id")
        await db.runs.create_index("status")

        # Tasks indexes: compound unique index per run ensures tasks don't collide across runs
        await db.tasks.create_index([("run_id", 1), ("task_id", 1)], unique=True)
        await db.tasks.create_index("task_id")
        await db.tasks.create_index("run_id")
        await db.tasks.create_index([("run_id", 1), ("status", 1)])

        # Approvals indexes
        await db.approvals.create_index("approval_id", unique=True)
        await db.approvals.create_index("task_id")
        await db.approvals.create_index("status")

        # Artifacts indexes
        await db.artifacts.create_index("artifact_id", unique=True)
        await db.artifacts.create_index("run_id")

        # RAG Documents indexes
        await db.documents.create_index("document_id", unique=True)
        await db.documents.create_index([("project_id", 1), ("created_at", -1)])
        await db.documents.create_index([("project_id", 1), ("content_hash", 1)])

        # RAG Project Embeddings indexes
        await db.project_embeddings.create_index("chunk_id", unique=True)
        await db.project_embeddings.create_index("document_id")
        await db.project_embeddings.create_index([("project_id", 1), ("allowed_roles", 1)])

        # Models registry
        await db.model_registry.create_index("model_id", unique=True)

        logger.info("MongoDB indexes verified and created successfully.")
    except Exception as e:
        logger.error(f"Error creating MongoDB indexes: {e}")
