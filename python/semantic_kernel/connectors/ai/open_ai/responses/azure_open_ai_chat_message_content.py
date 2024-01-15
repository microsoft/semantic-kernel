# Copyright (c) Microsoft. All rights reserved.


from typing import TYPE_CHECKING, Any, Dict, List, Optional

from openai.types.chat import ChatCompletion
from openai.types.chat.chat_completion import Choice

from semantic_kernel.connectors.ai.open_ai.models.chat.function_call import FunctionCall
from semantic_kernel.connectors.ai.open_ai.models.chat.tool_calls import ToolCall
from semantic_kernel.connectors.ai.open_ai.responses.open_ai_chat_message_content import OpenAIChatMessageContent

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.ai_request_settings import AIRequestSettings


class AzureOpenAIChatMessageContent(OpenAIChatMessageContent):
    """A chat response from Azure OpenAI."""

    tool_message: Optional[str] = None

    def __init__(
        self,
        choice: Choice,
        response: ChatCompletion,
        metadata: Dict[str, Any],
        request_settings: "AIRequestSettings",
        function_call: Optional[FunctionCall],
        tool_calls: Optional[List[ToolCall]],
        tool_message: Optional[str],
    ):
        """Initialize a chat response from Azure OpenAI."""
        super().__init__(
            choice=choice,
            response=response,
            metadata=metadata,
            request_settings=request_settings,
            function_call=function_call,
            tool_calls=tool_calls,
        )
        self.tool_message = tool_message
