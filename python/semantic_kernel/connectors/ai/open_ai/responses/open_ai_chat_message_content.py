# Copyright (c) Microsoft. All rights reserved.


from typing import TYPE_CHECKING, Any, Dict, List, Optional

from openai.types.chat import ChatCompletion
from openai.types.chat.chat_completion import Choice

from semantic_kernel.models.contents import ChatMessageContent

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.ai_request_settings import AIRequestSettings


class OpenAIChatMessageContent(ChatMessageContent):
    """A chat response from OpenAI."""

    inner_content: ChatCompletion
    function_call: Optional[Dict[str, Any]] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None

    def __init__(
        self,
        choice: Choice,
        response: ChatCompletion,
        metadata: Dict[str, Any],
        request_settings: "AIRequestSettings",
        function_call: Optional[Dict[str, Any]],
        tool_calls: Optional[List[Dict[str, Any]]],
    ):
        """Initialize a chat response from OpenAI."""
        super().__init__(
            inner_content=response,
            ai_model_id=request_settings.ai_model_id,
            role=choice.message.role,
            content=choice.message.content,
            metadata=metadata,
            function_call=function_call,
            tool_calls=tool_calls,
        )
