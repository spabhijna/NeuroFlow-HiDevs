import asyncio
import time
from typing import AsyncGenerator

from openai import (
    APIConnectionError,
    APITimeoutError,
    APIStatusError,
    AsyncOpenAI,
    AuthenticationError,
    RateLimitError,
)

from .base import BaseLLMProvider, ChatMessage, GenerationResult


PRICE_TABLE = {
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
}


class OpenAIProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model

    def _handle_openai_error(self, error: Exception) -> None:
        if isinstance(error, AuthenticationError):
            raise ValueError(
                "OpenAI authentication failed. Provide a valid API key via "
                "OPENAI_API_KEY or the api_key argument."
            ) from error
        if isinstance(error, RateLimitError):
            raise RuntimeError(
                "OpenAI rate limit exceeded. Please retry later."
            ) from error
        if isinstance(error, (APIConnectionError, APITimeoutError)):
            raise RuntimeError(
                "OpenAI request failed due to a network issue. Please retry."
            ) from error
        if isinstance(error, APIStatusError):
            status = getattr(error, "status_code", "unknown")
            raise RuntimeError(
                f"OpenAI API error (status {status})."
            ) from error

        raise error

    async def _retry(self, func, *args, **kwargs):
        retries = 3
        backoff = 1

        for attempt in range(retries):
            try:
                return await func(*args, **kwargs)
            except RateLimitError as e:
                if attempt == retries - 1:
                    raise
                wait = getattr(e, "retry_after", backoff)
                await asyncio.sleep(wait)
                backoff *= 2

    async def complete(self, messages: list[ChatMessage], **kwargs) -> GenerationResult:
        start = time.time()

        try:
            response = await self._retry(
                self.client.chat.completions.create,
                model=self.model,
                messages=[m.__dict__ for m in messages],
                **kwargs,
            )
        except Exception as error:
            self._handle_openai_error(error)

        latency = (time.time() - start) * 1000

        usage = response.usage
        input_tokens = usage.prompt_tokens
        output_tokens = usage.completion_tokens

        pricing = PRICE_TABLE[self.model]
        cost = (
            input_tokens * pricing["input"] +
            output_tokens * pricing["output"]
        ) / 1_000_000

        return GenerationResult(
            content=response.choices[0].message.content,
            model=self.model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency,
            cost_usd=cost,
            finish_reason=response.choices[0].finish_reason,
        )

    async def stream(self, messages: list[ChatMessage], **kwargs) -> AsyncGenerator[str, None]:
        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=[m.__dict__ for m in messages],
                stream=True,
                **kwargs,
            )
        except Exception as error:
            self._handle_openai_error(error)

        try:
            async for chunk in stream:
                delta = chunk.choices[0].delta
                if delta and delta.content:
                    yield delta.content
        except Exception as error:
            self._handle_openai_error(error)

    async def embed(self, texts: list[str]) -> list[list[float]]:
        batch_size = 100
        embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            try:
                response = await self.client.embeddings.create(
                    model="text-embedding-3-small",
                    input=batch,
                )
            except Exception as error:
                self._handle_openai_error(error)
            embeddings.extend([e.embedding for e in response.data])

        return embeddings

    @property
    def cost_per_input_token(self) -> float:
        return PRICE_TABLE[self.model]["input"] / 1_000_000

    @property
    def cost_per_output_token(self) -> float:
        return PRICE_TABLE[self.model]["output"] / 1_000_000

    @property
    def context_window(self) -> int:
        return 128_000