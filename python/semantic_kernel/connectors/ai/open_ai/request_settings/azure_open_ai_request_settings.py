import logging
from typing import Optional

from semantic_kernel.connectors.ai.open_ai.request_settings.open_ai_request_settings import (
    OpenAIChatRequestSettings,
)

_LOGGER = logging.getLogger(__name__)


class AzureOpenAIChatRequestSettings(OpenAIChatRequestSettings):
    """Specific settings for the Chat Completion endpoint."""

    response_format: Optional[str] = None
