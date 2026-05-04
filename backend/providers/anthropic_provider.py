import time
from typing import AsyncGenerator

from anthropic import AsyncAnthropic

from .base import BaseLLMProvider, ChatMessage, GenerationResult


class AnthropicProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model: str = "claude-3-haiku-20240307"):
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model

    def _split_messages(self, messages):
        system = None
        formatted = []

        for m in messages:
            if m.role == "system":
                system = m.content
            else:
                formatted.append({"role": m.role, "content": m.content})

        return system, formatted

    async def complete(self, messages: list[ChatMessage], **kwargs) -> GenerationResult:
        start = time.time()

        system, formatted = self._split_messages(messages)

        response = await self.client.messages.create(
            model=self.model,
            system=system,
            messages=formatted,
            **kwargs,
        )

        latency = (time.time() - start) * 1000

        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens

        return GenerationResult(
            content=response.content[0].text,
            model=self.model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency,
            cost_usd=0.0,  # plug pricing later
            finish_reason=response.stop_reason,
        )

    async def stream(self, messages: list[ChatMessage], **kwargs) -> AsyncGenerator[str, None]:
        system, formatted = self._split_messages(messages)

        stream = await self.client.messages.stream(
            model=self.model,
            system=system,
            messages=formatted,
            **kwargs,
        )

        async for event in stream:
            if event.type == "content_block_delta":
                yield event.delta.text

    async def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError("Anthropic does not support embeddings")

    @property
    def cost_per_input_token(self) -> float:
        return 0.0

    @property
    def cost_per_output_token(self) -> float:
        return 0.0

    @property
    def context_window(self) -> int:
        return 200_000