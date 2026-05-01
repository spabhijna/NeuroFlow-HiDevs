import json
import redis
from dataclasses import dataclass


@dataclass
class RoutingCriteria:
    task_type: str
    max_cost_per_call: float | None = None
    require_vision: bool = False
    require_long_context: bool = False
    latency_budget_ms: int | None = None
    prefer_fine_tuned: bool = False


class ModelRouter:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    def _load_models(self):
        data = self.redis.get("router:models")
        return json.loads(data) if data else []

    def route(self, criteria: RoutingCriteria):
        models = self._load_models()

        # Filter: vision
        if criteria.require_vision:
            models = [m for m in models if m.get("vision")]

        # Filter: long context
        if criteria.require_long_context:
            models = [m for m in models if m.get("context_window", 0) > 100_000]

        # Evaluation override
        if criteria.task_type == "evaluation":
            models = [m for m in models if m.get("is_judge")]

        # Fine-tuned preference
        if criteria.prefer_fine_tuned:
            ft_models = [m for m in models if m.get("fine_tuned")]
            if ft_models:
                models = ft_models

        # Cost filtering
        if criteria.max_cost_per_call is not None:
            models = [
                m for m in models
                if m.get("estimated_cost", 0) <= criteria.max_cost_per_call
            ]

        if not models:
            raise ValueError("No suitable model found")

        # Default: cheapest
        models.sort(key=lambda m: m.get("estimated_cost", float("inf")))

        return models[0]