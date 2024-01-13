# Copyright (c) Microsoft. All rights reserved.

from typing import AsyncGenerator, Dict, List, Optional, Union

from openai import AsyncStream
from openai.types import Completion
from openai.types.chat.chat_completion_chunk import Choice
from pydantic import PrivateAttr

from semantic_kernel.models.contents.kernel_content import KernelContent


class OpenAITextResponse(KernelContent):
    """A text completion response from OpenAI.

    For streaming responses, make sure to async loop through parse_stream before trying anything else.
    Once that is done:
    - content: get the content of first choice of the response.
    - all_content: get the content of all choices of the response.
    - parse_stream: get the streaming content of the response.
    """

    raw_response: Union[Completion, AsyncStream[Completion]]
    _parsed_content: Optional[Dict[str, str]] = PrivateAttr(default_factory=dict)

    @property
    def content(self) -> Optional[str]:
        """Get the content of the response.

        Content can be None when no text response was given, check if there are tool calls instead.
        """
        if not isinstance(self.raw_response, Completion):
            raise ValueError("content is not available for streaming responses, use stream_content instead.")
        return self.raw_response.choices[0].text

    @property
    def all_content(self) -> List[Optional[str]]:
        """Get the content of the response.

        Some or all content might be None, check if there are tool calls instead.
        """
        if not isinstance(self.raw_response, Completion):
            if self._parsed_content is not {}:
                return list(self._parsed_content.values())
            raise ValueError("all_content is not available for streaming responses, use stream_content instead.")
        return [choice.text for choice in self.raw_response.choices]

    async def parse_stream(self) -> AsyncGenerator[str, None]:
        """Get the streaming content of the response."""
        if isinstance(self.raw_response, Completion):
            raise ValueError("streaming_content is not available for regular responses, use content instead.")
        async for chunk in self.raw_response:
            if len(chunk.choices) == 0:
                continue
            for choice in chunk.choices:
                self.parse_choice(choice)
            if chunk.choices[0].delta.text:
                yield chunk.choices[0].delta.text

    def parse_choice(self, choice: Choice) -> None:
        """Parse a choice and store the text."""
        if choice.delta.content is not None:
            if choice.index in self._parsed_content:
                self._parsed_content[choice.index] += choice.delta.text
            else:
                self._parsed_content[choice.index] = choice.delta.text
