from typing import List, Dict, Any
from fastapi import APIRouter
from app.models.model_registry import ModelInfo, DEFAULT_MODELS
from app.services.model_adapter import model_adapter

router = APIRouter()


@router.get("/", response_model=List[ModelInfo])
async def list_models():
    ollama_ok = await model_adapter.check_ollama_health()
    available_list = await model_adapter.list_available_models()

    updated = []
    for m in DEFAULT_MODELS:
        m_copy = m.model_copy()
        if m.provider == "ollama":
            m_copy.is_available = ollama_ok
        updated.append(m_copy)
    return updated


@router.get("/status")
async def get_model_status() -> Dict[str, Any]:
    ollama_ok = await model_adapter.check_ollama_health()
    return {
        "ollama_connected": ollama_ok,
        "ollama_url": model_adapter.ollama_url,
        "gemini_api_configured": bool(model_adapter.gemini_key),
        "huggingface_configured": bool(model_adapter.hf_key),
        "mode": "hybrid_with_synthetic_fallback"
    }
