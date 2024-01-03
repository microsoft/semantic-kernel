# Copyright (c) Microsoft. All rights reserved.
"""Azure OpenAI Chat With Data Streaming Response class."""
from typing import Tuple

from openai import AsyncStream
from openai.types.chat import ChatCompletionChunk

from semantic_kernel.connectors.ai.open_ai.request_settings.azure_chat_request_settings import (
    AzureChatRequestSettings,
)


class AzureChatWithDataStreamResponse:
    """Class to hold Azure OpenAI Chat With Data streaming response."""

    _tool_message: str
    _assistant_message: AsyncStream[ChatCompletionChunk]
    _settings: "AzureChatRequestSettings"

    def __init__(
        self,
        assistant_message: AsyncStream[ChatCompletionChunk],
        settings: "AzureChatRequestSettings",
    ):
        self._assistant_message = assistant_message
        self._tool_message = ""
        self._settings = settings

    async def _iterate_to_assistant_message(self):
        """Iterate through the message stream to populate the tool message and stop at the assistant message."""
        while True:
            try:
                message = await self._assistant_message.__anext__()
                if message.choices and len(message.choices) > 0:
                    delta = message.choices[0].delta
                    if delta and delta.model_extra and "context" in delta.model_extra:
                        for m in delta.model_extra["context"].get("messages", []):
                            if m["role"] == "tool":
                                self._tool_message = m.get("content", "")
                                break
                        break
            except StopIteration:
                break

    async def get_tool_message(self):
        """Get the tool message."""
        if not self._tool_message:
            await self._iterate_to_assistant_message()

        return self._tool_message

    @staticmethod
    def _parse_choices(choice) -> Tuple[str, int]:
        message = ""
        if choice.delta.content:
            message += choice.delta.content

        return message, choice.index

    async def __aiter__(self):
        """Iterate through the message stream and yield the assistant response."""
        if not self._tool_message:
            await self._iterate_to_assistant_message()

        async for chunk in self._assistant_message:
            if len(chunk.choices) == 0:
                continue
            # if multiple responses are requested, keep track of them
            if self._settings.number_of_responses > 1:
                completions = [""] * self._settings.number_of_responses
                for choice in chunk.choices:
                    text, index = self._parse_choices(choice)
                    completions[index] = text
                yield completions
            # if only one response is requested, yield it
            else:
                text, index = self._parse_choices(chunk.choices[0])
                yield text
