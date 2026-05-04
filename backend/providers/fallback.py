class FallbackChain:
    def __init__(self, providers: list):
        self.providers = providers

    async def complete(self, messages, **kwargs):
        last_error = None

        for provider in self.providers:
            try:
                return await provider.complete(messages, **kwargs)
            except Exception as e:
                last_error = e
                # You might want logging here instead of silent suffering

        raise last_error

    async def stream(self, messages, **kwargs):
        last_error = None

        for provider in self.providers:
            try:
                async for token in provider.stream(messages, **kwargs):
                    yield token
                return
            except Exception as e:
                last_error = e

        raise last_error