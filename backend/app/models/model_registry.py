from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ModelInfo(BaseModel):
    model_id: str
    name: str
    provider: str  # "ollama", "gemini", "openai", "groq", "mock"
    family: str  # "qwen", "llama", "deepseek", "gemini", "gpt"
    capabilities: List[str] = Field(default_factory=list)  # ["coding", "reasoning", "general", "fast"]
    context_window: int = 8192
    avg_latency_ms: float = 1200.0
    cost_per_1k_tokens: float = 0.0
    is_local: bool = True
    is_available: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)


DEFAULT_MODELS: List[ModelInfo] = [
    ModelInfo(
        model_id="ollama/qwen2.5:latest",
        name="Qwen 2.5 (Local)",
        provider="ollama",
        family="qwen",
        capabilities=["coding", "reasoning", "general"],
        context_window=32768,
        avg_latency_ms=850.0,
        cost_per_1k_tokens=0.0,
        is_local=True,
        is_available=True
    ),
    ModelInfo(
        model_id="ollama/deepseek-coder:6.7b",
        name="DeepSeek Coder 6.7B (Local)",
        provider="ollama",
        family="deepseek",
        capabilities=["coding", "debugging"],
        context_window=16384,
        avg_latency_ms=950.0,
        cost_per_1k_tokens=0.0,
        is_local=True,
        is_available=True
    ),
    ModelInfo(
        model_id="ollama/llama3.2:latest",
        name="Llama 3.2 (Local)",
        provider="ollama",
        family="llama",
        capabilities=["reasoning", "writing", "general"],
        context_window=8192,
        avg_latency_ms=650.0,
        cost_per_1k_tokens=0.0,
        is_local=True,
        is_available=True
    ),
    ModelInfo(
        model_id="cloud/gemini-2.5-flash",
        name="Google Gemini 2.5 Flash (Cloud)",
        provider="gemini",
        family="gemini",
        capabilities=["coding", "reasoning", "multimodal", "fast"],
        context_window=1048576,
        avg_latency_ms=450.0,
        cost_per_1k_tokens=0.0001,
        is_local=False,
        is_available=True
    ),
    ModelInfo(
        model_id="huggingface/llama-3.1-8b",
        name="Hugging Face Llama 3.1 8B (Serverless)",
        provider="huggingface",
        family="llama",
        capabilities=["general", "fast", "reasoning"],
        context_window=128000,
        avg_latency_ms=750.0,
        cost_per_1k_tokens=0.0,
        is_local=False,
        is_available=True
    )
]
