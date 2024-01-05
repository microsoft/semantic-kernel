from typing import Any, AsyncGenerator

from semantic_kernel.connectors.ai.ai_request_settings import AIRequestSettings
from semantic_kernel.sk_pydantic import SKBaseModel


class AIResponse(SKBaseModel):
    raw_response: Any
    request_settings: AIRequestSettings

    @property
    def content(self) -> Any:
        """Get the content of the response."""
        return self.raw_response

    @property
    async def streaming_content(self) -> AsyncGenerator[Any, None]:
        """Get the streaming content of the response."""
        yield self.raw_response
