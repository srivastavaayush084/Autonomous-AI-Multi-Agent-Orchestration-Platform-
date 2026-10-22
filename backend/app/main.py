import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.database.mongodb import db_manager
from app.database.indexes import create_indexes
from app.api.api import api_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("multi_agent_platform")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Autonomous AI Multi-Agent Platform Backend...")
    await db_manager.connect()
    await create_indexes()
    yield
    logger.info("Shutting down Multi-Agent Platform Backend...")
    await db_manager.disconnect()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration: strict origin whitelisting for credentialed requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health", tags=["system"])
async def health_check():
    return {
        "status": "online",
        "version": settings.VERSION,
        "database": "connected" if db_manager.connected else "degraded_in_memory_fallback",
        "strategy": settings.ROUTER_STRATEGY,
        "mode": "hybrid_local_cloud"
    }


@app.get("/", tags=["system"])
async def root():
    return {
        "message": "Welcome to Autonomous AI Multi-Agent Orchestration Platform API",
        "docs": "/docs",
        "health": "/health"
    }
