# Copyright (c) Microsoft. All rights reserved.
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from openai.types.chat.chat_completion_chunk import ChatCompletionChunk, Choice

from semantic_kernel.connectors.ai.open_ai.responses.open_ai_streaming_chat_message_content import (
    OpenAIStreamingChatMessageContent,
)

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.ai_request_settings import AIRequestSettings


class AzureOpenAIStreamingChatMessageContent(OpenAIStreamingChatMessageContent):
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

    tool_message: Optional[str] = None

    def __init__(
        self,
        choice: Choice,
        chunk: ChatCompletionChunk,
        metadata: Dict[str, Any],
        request_settings: "AIRequestSettings",
        function_call: Optional[Dict[str, Any]],
        tool_calls: Optional[List[Dict[str, Any]]],
        tool_message: Optional[str],
    ):
        """Initialize a chat response from Azure OpenAI."""
        super().__init__(
            choice=choice,
            chunk=chunk,
            metadata=metadata,
            request_settings=request_settings,
            function_call=function_call,
            tool_calls=tool_calls,
        )
        self.tool_message = tool_message


# class AzureOpenAIStreamingChatMessageContent(OpenAIStreamingChatMessageContent):
#     """A response from OpenAI.

#     For streaming responses, make sure to async loop through parse_stream before trying anything else.
#     Once that is done:
#     - content: get the content of first choice of the response.
#     - all_content: get the content of all choices of the response.
#     - function_call: get the function call of first choice of the response.
#     - all_function_calls: get the function call of all choices of the response.
#     - tool_calls: get the tool calls of first choice of the response.
#     - all_tool_calls: get the tool calls of all choices of the response.
#     - parse_stream: get the streaming content of the response.
#     """

#     inner_content: Choice

#     def __str__(self) -> Optional[str]:
#         """Get the content of the response."""
#         return self.inner_content.delta.content

#     async def parse_stream(self) -> AsyncGenerator[str, None]:
#         """Get the streaming content of the response.

#         Any content, function calls and tool calls get parsed and stored in:
#         parsed_content, function_call and tool_calls dicts,
#         with the index of the choice as the key.

#         The first choice content is yielded as a stream.
#         """
#         if isinstance(self.raw_response, ChatCompletion):
#             raise ValueError("streaming_content is not available for regular responses, use content instead.")
#         async for chunk in self.raw_response:
#             if len(chunk.choices) == 0:
#                 continue
#             for choice in chunk.choices:
#                 self.parse_choice(choice)
#             if chunk.choices[0].delta.content:
#                 yield chunk.choices[0].delta.content

#     def parse_choice(self, choice: Choice) -> None:
#         """Parse a choice and store the content, function call and tool call."""
#         if choice.delta.tool_calls is not None:
#             if choice.index not in self._tool_calls:
#                 self._tool_calls[choice.index] = {}
#                 for tool in choice.delta.tool_calls:
#                     self._tool_calls[choice.index][tool.index] = {
#                         "id": tool.id,
#                         "type": tool.type,
#                         "function": FunctionCall(
#                             name=tool.function.name,
#                             arguments=tool.function.arguments if tool.function.arguments else "",
#                         ),
#                     }
#             else:
#                 for tool in choice.delta.tool_calls:
#                     if tool.index not in self._tool_calls[choice.index]:
#                         self._tool_calls[choice.index][tool.index] = {
#                             "id": tool.id,
#                             "type": tool.type,
#                             "function": FunctionCall(
#                                 name=tool.function.name,
#                                 arguments=tool.function.arguments if tool.function.arguments else "",
#                             ),
#                         }
#                     else:
#                         self._tool_calls[choice.index][tool.index]["function"].arguments += tool.function.arguments
#         if choice.delta.function_call is not None:
#             if choice.index in self._function_calls:
#                 self._function_calls[choice.index].arguments += choice.delta.function_call.arguments
#             else:
#                 self._function_calls[choice.index] = FunctionCall(
#                     name=choice.delta.function_call.name,
#                     arguments=choice.delta.function_call.arguments or "",
#                 )
#         if choice.delta.content is not None:
#             if choice.index in self._parsed_content:
#                 self._parsed_content[choice.index] += choice.delta.content
#             else:
#                 self._parsed_content[choice.index] = choice.delta.content
