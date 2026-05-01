from opentelemetry import trace


class NeuroFlowClient:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, router, providers: dict, redis_client):
        self.router = router
        self.providers = providers
        self.redis = redis_client
        self.tracer = trace.get_tracer(__name__)

    async def chat(self, messages, routing_criteria):
        model_config = self.router.route(routing_criteria)
        provider = self.providers[model_config["provider"]]

        with self.tracer.start_as_current_span("llm_call") as span:
            result = await provider.complete(messages)

            span.set_attribute("model", result.model)
            span.set_attribute("input_tokens", result.input_tokens)
            span.set_attribute("output_tokens", result.output_tokens)
            span.set_attribute("cost_usd", result.cost_usd)
            span.set_attribute("latency_ms", result.latency_ms)

            self._track_metrics(result)

            return result

    async def embed(self, texts):
        provider = self.providers["openai"]
        return await provider.embed(texts)

    def _track_metrics(self, result):
        model = result.model

        self.redis.incr(f"metrics:model:{model}:calls")
        self.redis.incrbyfloat(
            f"metrics:model:{model}:cost_usd",
            result.cost_usd,
        )