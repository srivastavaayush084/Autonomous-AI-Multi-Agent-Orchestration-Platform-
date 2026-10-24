import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Autonomous AI Multi-Agent Orchestration Platform"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000"
    ]
    
    # MongoDB Atlas
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "multi_agent_platform"
    
    # Inference Providers (Hybrid Mode)
    DEFAULT_MODEL_PROVIDER: str = "ollama"
    OLLAMA_BASE_URL: str = "http://127.0.0.1:11434"
    OLLAMA_DEFAULT_MODEL: str = "llama3.2:1b"
    PLANNER_MODEL: str = "llama3.2:1b"
    PLANNER_TIMEOUT_SECONDS: float = 30.0
    PLANNER_MAX_RETRIES: int = 2
    
    # Cloud API Fallbacks
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    HUGGINGFACE_API_KEY: str = ""
    
    # ML Router Configuration
    ROUTER_STRATEGY: str = "ml_hybrid"
    CONFIDENCE_THRESHOLD: float = 0.65
    
    # Security & Guardrails
    REQUIRE_HUMAN_APPROVAL_FOR_DESTRUCTIVE: bool = True
    EXECUTION_BUDGET_SECONDS: int = 300
    MAX_AGENT_RETRIES: int = 3

    model_config = SettingsConfigDict(
        env_file=[
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), ".env"),
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"),
            ".env"
        ],
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
