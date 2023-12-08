import logging
from typing import Any, Dict, List, Optional

from pydantic import field_validator

from semantic_kernel.connectors.ai.open_ai.const import DEFAULT_CHAT_SYSTEM_PROMPT
from semantic_kernel.connectors.ai.open_ai.open_ai_request_settings import (
    OpenAIChatRequestSettings,
)

_LOGGER = logging.getLogger(__name__)


class AzureOpenAIChatRequestSettings(OpenAIChatRequestSettings):
    """Specific settings for the Chat Completion endpoint."""

    response_format: Optional[str] = None
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[str] = None
    function_call: Optional[str] = None
    functions: Optional[List[Dict[str, Any]]] = None
    messages: Optional[List[Dict[str, Any]]] = [
        {"role": "system", "content": DEFAULT_CHAT_SYSTEM_PROMPT}
    ]

    @field_validator("function_call", "functions")
    @classmethod
    def validate_function_call(cls, v: Any):
        if v is not None:
            _LOGGER.warning(
                "The function_call and functions parameters are deprecated. Please use the tool_choice and tools parameters instead."  # noqa: E501
            )
