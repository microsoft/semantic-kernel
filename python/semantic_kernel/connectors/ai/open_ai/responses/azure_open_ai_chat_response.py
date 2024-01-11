# Copyright (c) Microsoft. All rights reserved.

from typing import Dict, List, Optional

from openai.types.chat import ChatCompletion
from openai.types.chat.chat_completion_chunk import Choice
from pydantic import PrivateAttr

from semantic_kernel.connectors.ai.open_ai.responses.open_ai_chat_response import OpenAIChatResponse


class AzureOpenAIChatResponse(OpenAIChatResponse):
    """A response from OpenAI.

    For streaming responses, make sure to async loop through parse_stream before trying anything else.
    Once that is done:
    - content: get the content of first choice of the response.
    - all_content: get the content of all choices of the response.
    - function_call: get the function call of first choice of the response.
    - all_function_calls: get the function call of all choices of the response.
    - tool_calls: get the tool calls of first choice of the response.
    - all_tool_calls: get the tool calls of all choices of the response.
    - tool_message: get the tool content of the first choice of the response, used when using the Extensions API.
    - all_tool_messages: get the tool content of all choices of the response, used when using the Extensions API.
    - parse_stream: get the streaming content of the response.
    """

    _tool_messages: Dict[int, List[Dict[str, str]]] = PrivateAttr(default_factory=dict)

    def parse_choice(self, choice: Choice) -> None:
        super().parse_choice(choice)
        if choice.delta.model_extra and "context" in choice.delta.model_extra:
            if choice.index in self._tool_messages:
                for extra_context in choice.delta.model_extra.get("context", {}).get("messages", []):
                    i = 00
                    for message in extra_context:
                        self._tool_messages[choice.index][0]["content"] += message.get("content", "")
                        i += 1
            else:
                for extra_context in choice.delta.model_extra.get("context", {}).get("messages", []):
                    self._tool_messages[choice.index] = extra_context

    @property
    def tool_messages(self) -> Optional[List[Dict[str, str]]]:
        """Get the tool content of the response."""
        if not isinstance(self.raw_response, ChatCompletion):
            if self._tool_messages is not None:
                return self._tool_messages[0]
            raise ValueError("tool_content is not available for streaming responses, use stream_tool_content instead.")
        if self._tool_messages:
            return self._tool_messages[0]
        for choice in self.raw_response.choices:
            if choice.message.model_extra and "context" in choice.message.model_extra:
                self._tool_messages[choice.index] = choice.message.model_extra["context"].get("messages", [])
        return self._tool_messages[0]

    @property
    def all_tool_messages(self) -> Optional[List[List[Dict[str, str]]]]:
        """Get the tool content of the response."""
        if not isinstance(self.raw_response, ChatCompletion):
            if self._tool_messages is not None:
                return list(self._tool_messages.values())
            raise ValueError("tool_content is not available for streaming responses, use stream_tool_content instead.")
        if self._tool_messages:
            return list(self._tool_messages.values())
        if self.raw_response.model_extra and "context" in self.raw_response.model_extra:
            return [m for m in self.raw_response.model_extra["context"].get("messages", {})]
