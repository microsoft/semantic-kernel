# Copyright (c) Microsoft. All rights reserved.

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from openai.types.chat.chat_completion_chunk import ChatCompletionChunk, Choice

from semantic_kernel.connectors.ai.open_ai.models.chat.function_call import FunctionCall
from semantic_kernel.connectors.ai.open_ai.models.chat.tool_calls import ToolCall
from semantic_kernel.models.contents import StreamingChatMessageContent

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.ai_request_settings import AIRequestSettings


class OpenAIStreamingChatMessageContent(StreamingChatMessageContent):
    """A response from OpenAI.

    For streaming responses, make sure to async loop through parse_stream before trying anything else.
    Once that is done:
    - content: get the content of first choice of the response.
    - all_content: get the content of all choices of the response.
    - function_call: get the function call of first choice of the response.
    - all_function_calls: get the function call of all choices of the response.
    - tool_calls: get the tool calls of first choice of the response.
    - all_tool_calls: get the tool calls of all choices of the response.
    - parse_stream: get the streaming content of the response.
    """

    inner_content: ChatCompletionChunk
    function_call: Optional[FunctionCall] = None
    tool_calls: Optional[List[ToolCall]] = None

    def __init__(
        self,
        choice: Choice,
        chunk: ChatCompletionChunk,
        metadata: Dict[str, Any],
        request_settings: "AIRequestSettings",
        function_call: Optional[FunctionCall],
        tool_calls: Optional[List[ToolCall]],
    ):
        """Initialize a chat response from OpenAI."""
        super().__init__(
            inner_content=chunk,
            ai_model_id=request_settings.ai_model_id,
            role=choice.delta.role,
            content=choice.delta.content,
            finish_reason=choice.finish_reason,
            metadata=metadata,
            function_call=function_call,
            tool_calls=tool_calls,
        )
