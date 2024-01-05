from typing import AsyncGenerator, Dict, List, Optional, Union

from openai import AsyncStream
from openai.types import Completion
from openai.types.chat import ChatCompletion, ChatCompletionChunk

from semantic_kernel.connectors.ai.ai_response import AIResponse
from semantic_kernel.connectors.ai.open_ai.models.chat.function_call import FunctionCall


class OpenAITextResponse(AIResponse):
    "A text completion response from OpenAI."

    raw_response: Union[Completion, AsyncStream[Completion]]
    stream_content: Optional[str] = None
    stream_all_content: Optional[List[str]] = None

    @property
    def content(self) -> Optional[str]:
        """Get the content of the response."""
        if not isinstance(self.raw_response, Completion):
            raise ValueError("content is not available for streaming responses, use stream_content instead.")
        return self.raw_response.choices[0].text

    @property
    def all_content(self) -> List[Optional[str]]:
        """Get the content of the response."""
        if not isinstance(self.raw_response, Completion):
            raise ValueError("all_content is not available for streaming responses, use stream_content instead.")
        return [choice.text for choice in self.raw_response.choices]

    async def streaming_content(self) -> AsyncGenerator[str, None]:
        """Get the streaming content of the response."""
        if isinstance(self.raw_response, Completion):
            raise ValueError("streaming_content is not available for regular responses, use content instead.")
        if self.stream_content is None:
            self.stream_content = ""
        async for chunk in self.raw_response:
            if len(chunk.choices) == 0:
                continue
            if chunk.choices[0].text:
                text = chunk.choices[0].text
                if text.strip():
                    self.stream_content += text
                    yield text

    async def streaming_all_content(self) -> AsyncGenerator[List[str], None]:
        """Get the streaming content of the response."""
        if isinstance(self.raw_response, Completion):
            raise ValueError("streaming_all_content is not available for regular responses, use all_content instead.")
        if self.stream_all_content is None:
            self.stream_all_content = [""] * self.request_settings.number_of_responses
        async for chunk in self.raw_response:
            if len(chunk.choices) == 0:
                continue
            current_chunks: List[str] = []
            for choice in chunk.choices:
                if choice.text:
                    text = choice.text
                    if text.strip():
                        self.stream_all_content[choice.index] += text
                        current_chunks.append(text)
            yield current_chunks


class OpenAIChatResponse(AIResponse):
    """A response from OpenAI."""

    raw_response: Union[ChatCompletion, AsyncStream[ChatCompletionChunk]]
    stream_content: Optional[str] = None
    stream_all_content: Optional[List[str]] = None

    @property
    def content(self) -> Optional[str]:
        """Get the content of the response."""
        if not isinstance(self.raw_response, ChatCompletion):
            raise ValueError("content is not available for streaming responses, use stream_content instead.")
        return self.raw_response.choices[0].message.content

    @property
    def function_call(self) -> Optional[FunctionCall]:
        """Get the function call of the response."""
        if not isinstance(self.raw_response, ChatCompletion):
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
    def tool_call(self) -> Optional[Dict[str, Dict[str, Union[str, FunctionCall]]]]:
        """Get the function call of the response."""
        if not isinstance(self.raw_response, ChatCompletion):
            raise ValueError("tool_call is not available for streaming responses, use stream_tool_call instead.")
        if (
            hasattr(self.raw_response.choices[0].message, "tool_calls")
            and self.raw_response.choices[0].message.tool_calls is not None
        ):
            tool_calls = self.raw_response.choices[0].message.tool_calls
            return {
                tool.id: {
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
    def all_content(self) -> List[Optional[str]]:
        """Get the content of the response."""
        if not isinstance(self.raw_response, ChatCompletion):
            raise ValueError("all_content is not available for streaming responses, use stream_content instead.")
        return [choice.message.content for choice in self.raw_response.choices]

    # TODO: consider using https://pypi.org/project/async-property/
    async def streaming_content(self) -> AsyncGenerator[str, None]:
        """Get the streaming content of the response."""
        if isinstance(self.raw_response, ChatCompletion):
            raise ValueError("streaming_content is not available for regular responses, use content instead.")
        if self.stream_content is None:
            self.stream_content = ""
        async for chunk in self.raw_response:
            if len(chunk.choices) == 0:
                continue
            if chunk.choices[0].delta.content:
                chunk_content = chunk.choices[0].delta.content
                self.stream_content += chunk_content
                yield chunk_content

    async def streaming_all_content(self) -> AsyncGenerator[List[str], None]:
        """Get the streaming content of the response."""
        if isinstance(self.raw_response, ChatCompletion):
            raise ValueError("streaming_all_content is not available for regular responses, use all_content instead.")
        if self.stream_all_content is None:
            self.stream_all_content = [""] * self.request_settings.number_of_responses
        async for chunk in self.raw_response:
            if len(chunk.choices) == 0:
                continue
            current_chunks: List[str] = []
            for choice in chunk.choices:
                if choice.delta.content:
                    chunk_content = choice.delta.content
                    self.stream_all_content[choice.index] += chunk_content
                    current_chunks.append(chunk_content)
            yield current_chunks


class AzureOpenAIChatResponse(OpenAIChatResponse):
    """A response from Azure OpenAI."""

    tool_message_content: Optional[str] = None

    async def _iterate_to_assistant_message(self):
        """Iterate through the message stream to populate the tool message and stop at the assistant message."""
        if isinstance(self.raw_response, ChatCompletion):
            raise ValueError(
                "_iterate_to_assistant_message is not available for streaming responses, use streaming_content instead."
            )
        while True:
            try:
                message = await self.raw_response.__anext__()
                if message.choices and len(message.choices) > 0:
                    delta = message.choices[0].delta
                    if delta and delta.model_extra and "context" in delta.model_extra:
                        for m in delta.model_extra["context"].get("messages", []):
                            if m["role"] == "tool":
                                self.tool_message_content = m.get("content", "")
                                break
                        break
            except StopIteration:
                break

    async def streaming_tool_message(self):
        """Get the tool message."""
        if not isinstance(self.raw_response, ChatCompletion):
            raise ValueError("streaming_tool_message is not available for regular responses, use tool_message instead.")
        if not self.tool_message_content:
            await self._iterate_to_assistant_message()
        return self.tool_message_content

    @property
    def tool_message(self) -> Optional[str]:
        """Get the tool content of the response."""
        if not isinstance(self.raw_response, ChatCompletion):
            raise ValueError("tool_content is not available for streaming responses, use stream_tool_content instead.")
        if self.tool_message_content:
            return self.tool_message_content
        if self.raw_response.model_extra and "context" in self.raw_response.model_extra:
            for m in self.raw_response.model_extra["context"].get("messages", {}):
                if m["role"] == "tool":
                    self.tool_message_content = m.get("content", None)
                    return self.tool_message_content

    async def streaming_content(self) -> AsyncGenerator[str, None]:
        """Get the streaming content of the response."""
        if not self.tool_message:
            await self._iterate_to_assistant_message()
        return super().streaming_content()
