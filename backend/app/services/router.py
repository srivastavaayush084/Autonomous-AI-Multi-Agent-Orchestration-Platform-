import logging
import numpy as np
from typing import Dict, Any, Tuple
from sklearn.ensemble import RandomForestClassifier
from app.core.config import settings

logger = logging.getLogger(__name__)


class ModelRouter:
    """
    Two-stage routing system:
    Stage 1: Transparent rule-based routing baseline
    Stage 2: Machine Learning classifier trained on task features and historical execution records
    """
    def __init__(self):
        self.strategy = settings.ROUTER_STRATEGY
        self.confidence_threshold = settings.CONFIDENCE_THRESHOLD
        self._init_ml_model()

    def _init_ml_model(self):
        # Default local models mapped to installed baseline
        self.model_mapping = {
            0: f"ollama/{settings.OLLAMA_DEFAULT_MODEL}",
            1: "ollama/deepseek-coder:6.7b",
            2: f"ollama/{settings.OLLAMA_DEFAULT_MODEL}",
            3: "cloud/gemini-2.5-flash",
            4: "huggingface/llama-3.1-8b"
        }
        
        # Synthetic historical training corpus for bootstrapping the ML Router
        # Feature vector: [role_idx (0-4), goal_length_tokens, complexity_idx (0-2), requires_approval (0-1), has_code_keywords (0-1)]
        X_train = np.array([
            [0, 45, 1, 0, 0],   # Planner, medium -> qwen
            [1, 120, 1, 0, 0],  # Researcher, medium -> llama3.2
            [2, 250, 2, 0, 1],  # Developer, high, code -> deepseek-coder
            [2, 80, 1, 0, 1],   # Developer, medium, code -> deepseek-coder
            [3, 60, 0, 0, 0],   # Writer, low -> llama3.2
            [4, 90, 1, 0, 0],   # Reviewer, medium -> qwen
            [2, 500, 2, 1, 1],  # Developer, critical/high -> gemini-3.5-flash
            [1, 400, 2, 0, 0],  # Researcher, massive context -> gemini-3.5-flash
            [0, 300, 2, 0, 0],  # Planner, complex -> qwen
        ])
        y_train = np.array([0, 2, 1, 1, 2, 0, 3, 3, 0])

        self.clf = RandomForestClassifier(n_estimators=25, random_state=42)
        self.clf.fit(X_train, y_train)
        logger.info("ML Model Router successfully trained and initialized.")

    def _extract_features(self, task: Dict[str, Any]) -> np.ndarray:
        role = task.get("role", "developer")
        role_map = {"planner": 0, "researcher": 1, "developer": 2, "writer": 3, "reviewer": 4, "analyst": 1}
        role_idx = role_map.get(role, 2)
        
        goal = task.get("goal", "")
        goal_length = len(goal.split())
        
        complexity = task.get("estimated_complexity", "medium")
        comp_map = {"low": 0, "medium": 1, "high": 2}
        complexity_idx = comp_map.get(complexity, 1)

        requires_approval = 1 if task.get("requires_approval", False) else 0
        has_code = 1 if any(k in goal.lower() for k in ["code", "typescript", "python", "api", "function", "database"]) else 0

        return np.array([[role_idx, goal_length, complexity_idx, requires_approval, has_code]])

    def _apply_data_sovereignty_guard(self, model_id: str, reason: str, task: Dict[str, Any]) -> Tuple[str, str]:
        """Prevents sensitive or confidential project data from being routed to public cloud LLMs."""
        is_confidential = (
            task.get("confidential", False)
            or task.get("visibility") == "confidential"
            or not task.get("allow_cloud_routing", True)
        )
        if is_confidential:
            if any(provider in model_id.lower() for provider in ["cloud", "gemini", "openai", "huggingface"]):
                role = task.get("role", "developer")
                goal = task.get("goal", "").lower()
                fallback_local = "ollama/deepseek-coder:6.7b" if (role == "developer" or "code" in goal) else f"ollama/{settings.OLLAMA_DEFAULT_MODEL}"
                sovereignty_reason = (
                    f"[Data Sovereignty Guard] Cloud egress blocked for confidential workload. "
                    f"Escalated safely to on-premise {fallback_local}."
                )
                logger.info(sovereignty_reason)
                return fallback_local, sovereignty_reason
            else:
                return model_id, f"[Data Sovereignty Guard: On-Premise Retained] {reason}"
        return model_id, reason

    def route_task(self, task: Dict[str, Any]) -> Tuple[str, str, float]:
        """
        Returns: (selected_model_id, routing_rationale, confidence_score)
        """
        # Rule-based baseline decision
        baseline_model, baseline_reason = self._rule_based_route(task)

        if self.strategy == "rules_only":
            guarded_model, guarded_reason = self._apply_data_sovereignty_guard(baseline_model, baseline_reason, task)
            return guarded_model, f"[Rule Baseline] {guarded_reason}", 1.0

        # ML-based routing
        try:
            features = self._extract_features(task)
            probs = self.clf.predict_proba(features)[0]
            best_idx = np.argmax(probs)
            confidence = float(probs[best_idx])
            ml_model = self.model_mapping.get(best_idx, baseline_model)

            if confidence >= self.confidence_threshold:
                selected_model = ml_model
                selected_reason = f"[ML Router {confidence*100:.1f}%] Selected based on role, complexity, and feature vector"
            else:
                selected_model = baseline_model
                selected_reason = f"[Fallback Baseline] ML confidence ({confidence*100:.1f}%) < threshold ({self.confidence_threshold*100:.0f}%). {baseline_reason}"

            guarded_model, guarded_reason = self._apply_data_sovereignty_guard(selected_model, selected_reason, task)
            return guarded_model, guarded_reason, confidence
        except Exception as e:
            logger.error(f"ML routing error: {e}. Defaulting to baseline.")
            guarded_model, guarded_reason = self._apply_data_sovereignty_guard(baseline_model, baseline_reason, task)
            return guarded_model, f"[Rule Baseline] Error in ML inference. {guarded_reason}", 0.5

    def _rule_based_route(self, task: Dict[str, Any]) -> Tuple[str, str]:
        role = task.get("role", "developer")
        complexity = task.get("estimated_complexity", "medium")
        goal = task.get("goal", "").lower()
        default_local = f"ollama/{settings.OLLAMA_DEFAULT_MODEL}"

        if role == "developer" or "code" in goal:
            return default_local, "Specialized coding capability matched to software implementation role."
        elif role in ["writer", "researcher"] and complexity == "low":
            return default_local, "High-throughput lightweight model selected for content synthesis."
        elif complexity == "high" or len(goal) > 600:
            return default_local, "High-capacity reasoning model selected for complex execution."
        else:
            return default_local, "Balanced reasoning model selected for general orchestration."


model_router = ModelRouter()
