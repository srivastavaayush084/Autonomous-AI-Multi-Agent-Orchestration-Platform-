import logging
import json
import httpx
from typing import Optional, Dict, Any, List
from app.core.config import settings

logger = logging.getLogger(__name__)


class ModelAdapter:
    def __init__(self):
        self.ollama_url = settings.OLLAMA_BASE_URL.rstrip('/')
        self.gemini_key = settings.GEMINI_API_KEY
        self.openai_key = settings.OPENAI_API_KEY
        self.hf_key = settings.HUGGINGFACE_API_KEY

    async def check_ollama_health(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                res = await client.get(f"{self.ollama_url}/api/tags")
                return res.status_code == 200
        except Exception:
            return False

    async def list_available_models(self) -> List[str]:
        models = []
        # Check Ollama
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                res = await client.get(f"{self.ollama_url}/api/tags")
                if res.status_code == 200:
                    data = res.json()
                    models.extend([f"ollama/{m['name']}" for m in data.get("models", [])])
        except Exception:
            pass

        if self.gemini_key:
            models.append("cloud/gemini-2.5-flash")
        if self.openai_key:
            models.append("cloud/gpt-4o-mini")

        if not models:
            models.append("ollama/qwen2.5:latest")
            models.append("cloud/gemini-2.5-flash")

        return models

    async def generate(self, model_id: str, system_prompt: str, user_prompt: str, temperature: float = 0.2) -> str:
        """
        Executes generation with automatic fallback:
        1. Targeted model (Ollama or Cloud)
        2. Fallback provider if targeted provider fails
        3. Built-in resilient reasoning engine for offline/demo reliability
        """
        provider = "ollama" if "ollama" in model_id.lower() else "cloud"
        clean_model = model_id.split("/")[-1]

        # Direct Provider: Hugging Face
        if "huggingface" in model_id.lower() and self.hf_key:
            try:
                hf_url = "https://router.huggingface.co/v1/chat/completions"
                headers = {"Authorization": f"Bearer {self.hf_key}"}
                hf_model = "meta-llama/Llama-3.1-8B-Instruct"
                async with httpx.AsyncClient(timeout=30.0) as client:
                    payload = {
                        "model": hf_model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "temperature": temperature,
                        "max_tokens": 1500
                    }
                    res = await client.post(hf_url, headers=headers, json=payload)
                    if res.status_code == 200:
                        data = res.json()
                        choices = data.get("choices", [])
                        if choices:
                            return choices[0]["message"]["content"]
                    else:
                        logger.warning(f"Hugging Face returned status {res.status_code}: {res.text[:150]}")
            except Exception as e:
                logger.warning(f"Hugging Face request failed: {e}")

    async def _resolve_ollama_model(self, requested_model: str) -> str:
        """
        Resolves requested model to an installed model in Ollama.
        If requested model is not installed, falls back to settings.OLLAMA_DEFAULT_MODEL or the first installed model.
        """
        clean_model = requested_model.split("/")[-1]
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(4.0, connect=2.0)) as client:
                res = await client.get(f"{self.ollama_url}/api/tags")
                if res.status_code == 200:
                    installed = [m.get("name", "") for m in res.json().get("models", [])]
                    if not installed:
                        return clean_model
                    if clean_model in installed:
                        return clean_model
                    clean_base = clean_model.split(":")[0]
                    for m in installed:
                        if m.split(":")[0] == clean_base:
                            return m
                    if settings.OLLAMA_DEFAULT_MODEL in installed:
                        logger.info(f"Ollama model '{clean_model}' not installed. Resolved to default '{settings.OLLAMA_DEFAULT_MODEL}'.")
                        return settings.OLLAMA_DEFAULT_MODEL
                    logger.info(f"Ollama model '{clean_model}' not installed. Resolved to available '{installed[0]}'.")
                    return installed[0]
        except Exception as e:
            logger.debug(f"Could not query Ollama tags: {e}")
        return clean_model

    async def generate(
        self,
        model_id: str,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
        timeout: Optional[float] = None,
    ) -> str:
        """
        Executes generation with automatic fallback:
        1. Targeted model (Ollama or Cloud) with dynamic model resolution
        2. Fallback provider if targeted provider fails
        3. Clear, explicit error handling if all providers are unavailable
        """
        provider = "ollama" if "ollama" in model_id.lower() else "cloud"
        clean_model = model_id.split("/")[-1]

        # Attempt 1: Direct Provider - Hugging Face (if targeted or key present)
        if "huggingface" in model_id.lower() and self.hf_key and not self.hf_key.startswith("hf_placeholder"):
            try:
                hf_url = "https://router.huggingface.co/v1/chat/completions"
                headers = {"Authorization": f"Bearer {self.hf_key}"}
                hf_model = "meta-llama/Llama-3.1-8B-Instruct"
                async with httpx.AsyncClient(timeout=30.0) as client:
                    payload = {
                        "model": hf_model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "temperature": temperature,
                        "max_tokens": 1500
                    }
                    res = await client.post(hf_url, headers=headers, json=payload)
                    if res.status_code == 200:
                        data = res.json()
                        choices = data.get("choices", [])
                        if choices:
                            return choices[0]["message"]["content"]
            except Exception as e:
                logger.warning(f"Hugging Face request failed: {e}")

        # Attempt 2: Direct Provider - Cloud (Gemini) if targeted
        if ("cloud" in model_id.lower() or "gemini" in model_id.lower()) and self.gemini_key and not self.gemini_key.startswith("AQ."):
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={self.gemini_key}"
                async with httpx.AsyncClient(timeout=30.0) as client:
                    payload = {
                        "contents": [
                            {"role": "user", "parts": [{"text": f"System: {system_prompt}\n\nTask: {user_prompt}"}]}
                        ],
                        "generationConfig": {"temperature": temperature}
                    }
                    res = await client.post(url, json=payload)
                    if res.status_code == 200:
                        candidates = res.json().get("candidates", [])
                        if candidates:
                            return candidates[0]["content"]["parts"][0]["text"]
            except Exception as e:
                logger.warning(f"Gemini generation failed: {e}")

        # Attempt 3: Local Ollama (targeted, or as fallback from failed cloud/offline model)
        try:
            target_model = await self._resolve_ollama_model(clean_model)
            timeout_sec = timeout or float(settings.EXECUTION_BUDGET_SECONDS)  # default 300.0s
            options: Dict[str, Any] = {"temperature": temperature}
            if max_tokens:
                options["num_predict"] = max_tokens

            async with httpx.AsyncClient(timeout=httpx.Timeout(timeout_sec, connect=5.0)) as client:
                payload = {
                    "model": target_model,
                    "prompt": user_prompt,
                    "system": system_prompt,
                    "stream": False,
                    "options": options
                }
                res = await client.post(f"{self.ollama_url}/api/generate", json=payload)
                if res.status_code == 200:
                    content = res.json().get("response", "").strip()
                    if content:
                        return content
                else:
                    logger.warning(f"Ollama returned status {res.status_code} for {target_model}: {res.text[:150]}")
        except Exception as e:
            logger.warning(f"Ollama generation failed for {clean_model}: {e}")

        # All providers failed: return explicit error indicator (never false canned success)
        err_msg = f"[ERROR: Model inference failed for '{model_id}': local Ollama and cloud providers unavailable or timed out.]"
        logger.error(err_msg)
        return err_msg

    async def chat_structured(
        self,
        model_id: str,
        system_prompt: str,
        user_prompt: str,
        json_schema: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Sends structured chat request using Ollama's /api/chat endpoint with JSON Schema constraints.
        Returns parsed dict. Raises ValueError or httpx exceptions on failure.
        """
        clean_model = model_id.split("/")[-1]
        timeout_sec = timeout or settings.PLANNER_TIMEOUT_SECONDS

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(timeout_sec, connect=3.0)) as client:
                payload: Dict[str, Any] = {
                    "model": clean_model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "stream": False,
                    "options": {"temperature": 0.0}
                }
                if json_schema:
                    payload["format"] = json_schema
                else:
                    payload["format"] = "json"

                res = await client.post(f"{self.ollama_url}/api/chat", json=payload)
                if res.status_code == 200:
                    data = res.json()
                    msg = data.get("message", {}).get("content", "")
                    clean_content = msg.strip()
                    if "```" in clean_content:
                        parts = clean_content.split("```")
                        for part in parts:
                            cand = part.strip()
                            if cand.startswith("json"):
                                cand = cand[4:].strip()
                            if cand.startswith("{") and cand.endswith("}"):
                                clean_content = cand
                                break
                    return json.loads(clean_content)
                else:
                    logger.warning(f"Ollama chat_structured returned status {res.status_code}: {res.text[:150]}")
                    raise RuntimeError(f"Ollama returned status {res.status_code}: {res.text[:150]}")
        except Exception as e:
            logger.warning(f"Ollama chat_structured failed for {clean_model}: {e}")
            raise

    def _generate_synthetic_response(self, system_prompt: str, user_prompt: str) -> str:
        """
        Deprecated. Canned placeholder fallbacks have been eliminated.
        Explicit errors are raised instead to prevent false success.
        """
        raise RuntimeError("Synthetic placeholder content has been disabled. Genuine model response required.")


model_adapter = ModelAdapter()
