# Copyright (c) Microsoft. All rights reserved.

from typing import AsyncGenerator, Dict, List, Optional, Union

from openai.types.chat import ChatCompletion
from openai.types.chat.chat_completion_chunk import Choice
from pydantic import PrivateAttr

from semantic_kernel.connectors.ai.open_ai.models.chat.function_call import FunctionCall
from semantic_kernel.models.contents import ChatMessageContent


class OpenAIChatMessageContent(ChatMessageContent):
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

    inner_content: ChatCompletion
    _parsed_content: Dict[int, str] = PrivateAttr(default_factory=dict)
    _function_calls: Dict[int, Optional[FunctionCall]] = PrivateAttr(default_factory=dict)
    _tool_calls: Dict[int, Dict[int, Dict[str, Union[str, FunctionCall]]]] = PrivateAttr(default_factory=dict)

    def __str__(self) -> Optional[str]:
        """Get the content of the response."""
        if not isinstance(self.raw_response, ChatCompletion):
            if self._parsed_content is not None:
                return self._parsed_content.get(0, None)
            raise ValueError("content is not available for streaming responses, use stream_content instead.")
        return self.inner_content.choices[0].message.content

    @property
    def all_content(self) -> List[Optional[str]]:
        """Get the content of the response."""
        if not isinstance(self.raw_response, ChatCompletion):
            if self._parsed_content is not None:
                return list(self._parsed_content.values())
            raise ValueError("all_content is not available for streaming responses, use stream_content instead.")
        return [choice.message.content for choice in self.raw_response.choices]

    @property
    def function_call(self) -> Optional[FunctionCall]:
        """Get the function call of the response."""
        if not isinstance(self.raw_response, ChatCompletion):
            if self._function_calls is not None:
                return self._function_calls.get(0, None)
            raise ValueError(
                "function_call is not available for streaming responses, use stream_function_call instead."
            )
        if (
            hasattr(self.raw_response.choices[0].message, "function_call")
            and self.raw_response.choices[0].message.function_call is not None
        ):
            return FunctionCall(
                name=self.raw_response.choices[0].message.function_call.name,
                arguments=self.raw_response.choices[0].message.function_call.arguments,
            )
        return None

    @property
    def all_function_calls(self) -> List[Optional[FunctionCall]]:
        """Get the function call of the response."""
        if not isinstance(self.raw_response, ChatCompletion):
            if self._function_calls is not None:
                return list(self._function_calls.values())
            raise ValueError(
                "function_call is not available for streaming responses, use stream_function_call instead."
            )
        return [
            FunctionCall(
                name=choice.message.function_call.name,
                arguments=choice.message.function_call.arguments,
            )
            for choice in self.raw_response.choices
        ]

    @property
    def tool_calls(self) -> Optional[Dict[int, Dict[str, Union[str, FunctionCall]]]]:
        """Get the function call of the response."""
        if not isinstance(self.raw_response, ChatCompletion):
            if self._tool_calls is not None:
                return self._tool_calls.get(0, None)
            raise ValueError(
                "To get the tool call of a streaming response, parse the stream first, with parse_stream()."
            )
        if (
            hasattr(self.raw_response.choices[0].message, "tool_calls")
            and self.raw_response.choices[0].message.tool_calls is not None
        ):
            tool_calls = self.raw_response.choices[0].message.tool_calls
            return {
                tool.index: {
                    "id": tool.id,
                    "type": tool.type,
                    "function": FunctionCall(
                        name=tool.function.name,
                        arguments=tool.function.arguments,
                    ),
                }
                for tool in tool_calls
            }
        return None

    @property
    def all_tool_calls(self) -> List[Optional[Dict[int, Dict[str, Union[str, FunctionCall]]]]]:
        """Get the function call of the response."""
        if not isinstance(self.raw_response, ChatCompletion):
            if self._tool_calls is not None:
                return list(self._tool_calls.values())
            raise ValueError("tool_call is not available for streaming responses, use stream_tool_call instead.")
        return [
            {
                tool.index: {
                    "id": tool.id,
                    "type": tool.type,
                    "function": FunctionCall(
                        name=tool.function.name,
                        arguments=tool.function.arguments,
                    ),
                }
                for tool in choice.message.tool_calls
            }
            for choice in self.raw_response.choices
        ]

    async def parse_stream(self) -> AsyncGenerator[str, None]:
        """Get the streaming content of the response.

        Any content, function calls and tool calls get parsed and stored in:
        parsed_content, function_call and tool_calls dicts,
        with the index of the choice as the key.

        The first choice content is yielded as a stream.
        """
        if isinstance(self.raw_response, ChatCompletion):
            raise ValueError("streaming_content is not available for regular responses, use content instead.")
        async for chunk in self.raw_response:
            if len(chunk.choices) == 0:
                continue
            for choice in chunk.choices:
                self.parse_choice(choice)
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def parse_choice(self, choice: Choice) -> None:
        """Parse a choice and store the content, function call and tool call."""
        if choice.delta.tool_calls is not None:
            if choice.index not in self._tool_calls:
                self._tool_calls[choice.index] = {}
                for tool in choice.delta.tool_calls:
                    self._tool_calls[choice.index][tool.index] = {
                        "id": tool.id,
                        "type": tool.type,
                        "function": FunctionCall(
                            name=tool.function.name,
                            arguments=tool.function.arguments if tool.function.arguments else "",
                        ),
                    }
            else:
                for tool in choice.delta.tool_calls:
                    if tool.index not in self._tool_calls[choice.index]:
                        self._tool_calls[choice.index][tool.index] = {
                            "id": tool.id,
                            "type": tool.type,
                            "function": FunctionCall(
                                name=tool.function.name,
                                arguments=tool.function.arguments if tool.function.arguments else "",
                            ),
                        }
                    else:
                        self._tool_calls[choice.index][tool.index]["function"].arguments += tool.function.arguments
        if choice.delta.function_call is not None:
            if choice.index in self._function_calls:
                self._function_calls[choice.index].arguments += choice.delta.function_call.arguments
            else:
                self._function_calls[choice.index] = FunctionCall(
                    name=choice.delta.function_call.name,
                    arguments=choice.delta.function_call.arguments or "",
                )
        if choice.delta.content is not None:
            if choice.index in self._parsed_content:
                self._parsed_content[choice.index] += choice.delta.content
            else:
                self._parsed_content[choice.index] = choice.delta.content
