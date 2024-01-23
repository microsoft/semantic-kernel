# Copyright (c) Microsoft. All rights reserved.

import logging
from collections.abc import AsyncIterable
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Union,
)

from openai import AsyncStream
from openai.types.chat.chat_completion import ChatCompletion, Choice
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk
from openai.types.chat.chat_completion_chunk import Choice as ChunkChoice

from semantic_kernel.connectors.ai.ai_request_settings import AIRequestSettings
from semantic_kernel.connectors.ai.chat_completion_client_base import (
    ChatCompletionClientBase,
)
from semantic_kernel.connectors.ai.open_ai.contents import OpenAIChatMessageContent, OpenAIStreamingChatMessageContent
from semantic_kernel.connectors.ai.open_ai.models.chat.function_call import FunctionCall
from semantic_kernel.connectors.ai.open_ai.models.chat.tool_calls import ToolCall
from semantic_kernel.connectors.ai.open_ai.request_settings.open_ai_request_settings import (
    OpenAIChatRequestSettings,
    OpenAIRequestSettings,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_handler import OpenAIHandler

logger: logging.Logger = logging.getLogger(__name__)


class OpenAIChatCompletionBase(OpenAIHandler, ChatCompletionClientBase):
    """OpenAI Chat completion class."""

    def get_request_settings_class(self) -> "AIRequestSettings":
        """Create a request settings object."""
        return OpenAIChatRequestSettings

    async def complete_chat_async(
        self,
        messages: List[Dict[str, str]],
        settings: OpenAIRequestSettings,
        **kwargs,
    ) -> List[OpenAIChatMessageContent]:
        """Executes a chat completion request and returns the result.

        Arguments:
            # TODO: replace messages with ChatHistory object with ChatMessageContent objects
            messages {List[Dict[str,str]]} -- The messages to use for the chat completion.
            settings {OpenAIRequestSettings} -- The settings to use for the chat completion request.
            logger {Optional[Logger]} -- The logger instance to use. (Deprecated)

        Returns:
            Union[str, List[str]] -- The completion result(s).
        """
        settings.messages = messages
        settings.stream = False
        if not settings.ai_model_id:
            settings.ai_model_id = self.ai_model_id
        response = await self._send_request(request_settings=settings)
        response_metadata = self.get_metadata_from_chat_response(response)
        return [self._create_return_content(response, choice, response_metadata) for choice in response.choices]

    async def complete_chat_stream_async(
        self,
        messages: List[Dict[str, str]],
        settings: OpenAIRequestSettings,
        **kwargs,
    ) -> AsyncIterable[List[OpenAIStreamingChatMessageContent]]:
        """Executes a chat completion request and returns the result.

        Arguments:
            messages {List[Tuple[str,str]]} -- The messages to use for the chat completion.
            settings {OpenAIRequestSettings} -- The settings to use for the chat completion request.
            logger {Optional[Logger]} -- The logger instance to use. (Deprecated)

        Returns:
            Union[str, List[str]] -- The completion result(s).
        """
        settings.messages = messages
        settings.stream = True
        if not settings.ai_model_id:
            settings.ai_model_id = self.ai_model_id
        response = await self._send_request(request_settings=settings)
        if not isinstance(response, AsyncStream):
            raise ValueError("Expected an AsyncStream[ChatCompletionChunk] response.")

        update_storage = self._get_update_storage_fields()

        async for chunk in response:
            if len(chunk.choices) == 0:
                continue
            chunk_metadata = self.get_metadata_from_streaming_chat_response(chunk)
            contents = [self._create_return_content_stream(chunk, choice, chunk_metadata) for choice in chunk.choices]
            self._handle_updates(contents, update_storage)
            yield contents

    def _create_return_content(
        self, response: ChatCompletion, choice: Choice, response_metadata: Dict[str, Any]
    ) -> OpenAIChatMessageContent:
        metadata = self.get_metadata_from_chat_choice(choice)
        metadata.update(response_metadata)
        return OpenAIChatMessageContent(
            inner_content=response,
            ai_model_id=self.ai_model_id,
            metadata=metadata,
            role=choice.message.role,
            content=choice.message.content,
            function_call=self.get_function_call_from_chat_choice(choice),
            tool_calls=self.get_tool_calls_from_chat_choice(choice),
        )

    def _create_return_content_stream(
        self,
        chunk: ChatCompletionChunk,
        choice: ChunkChoice,
        chunk_metadata: Dict[str, Any],
    ):
        metadata = self.get_metadata_from_chat_choice(choice)
        metadata.update(chunk_metadata)
        return OpenAIStreamingChatMessageContent(
            choice_index=choice.index,
            inner_content=chunk,
            ai_model_id=self.ai_model_id,
            metadata=metadata,
            role=choice.delta.role,
            content=choice.delta.content,
            finish_reason=choice.finish_reason,
            function_call=self.get_function_call_from_chat_choice(choice),
            tool_calls=self.get_tool_calls_from_chat_choice(choice),
        )

    def _get_update_storage_fields(self) -> Dict[str, Dict[int, Any]]:
        out_messages = {}
        tool_call_ids_by_index = {}
        function_call_by_index = {}
        return {
            "out_messages": out_messages,
            "tool_call_ids_by_index": tool_call_ids_by_index,
            "function_call_by_index": function_call_by_index,
        }

    def _handle_updates(
        self, contents: List[OpenAIStreamingChatMessageContent], update_storage: Dict[str, Dict[int, Any]]
    ):
        """Handle updates to the messages, tool_calls and function_calls.

        This will be used for auto-invoking tools.
        """
        out_messages = update_storage["out_messages"]
        tool_call_ids_by_index = update_storage["tool_call_ids_by_index"]
        function_call_by_index = update_storage["function_call_by_index"]

        for index, content in enumerate(contents):
            if content.content is not None:
                if index not in out_messages:
                    out_messages[index] = str(content)
                else:
                    out_messages[index] += str(content)
            if content.tool_calls is not None:
                if index not in tool_call_ids_by_index:
                    tool_call_ids_by_index[index] = content.tool_calls
                else:
                    for tc_index, tool_call in enumerate(content.tool_calls):
                        tool_call_ids_by_index[index][tc_index].update(tool_call)
            if content.function_call is not None:
                if index not in function_call_by_index:
                    function_call_by_index[index] = content.function_call
                else:
                    function_call_by_index[index].update(content.function_call)

    def get_metadata_from_chat_response(self, response: ChatCompletion) -> Dict[str, Any]:
        return {
            "id": response.id,
            "created": response.created,
            "system_fingerprint": response.system_fingerprint,
            "usage": response.usage,
        }

    def get_metadata_from_streaming_chat_response(self, response: ChatCompletionChunk) -> Dict[str, Any]:
        return {
            "id": response.id,
            "created": response.created,
            "system_fingerprint": response.system_fingerprint,
        }

    def get_metadata_from_chat_choice(self, choice: Union[Choice, ChunkChoice]) -> Dict[str, Any]:
        return {
            "logprobs": choice.logprobs,
        }

    def get_tool_calls_from_chat_choice(self, choice: Union[Choice, ChunkChoice]) -> Optional[List[ToolCall]]:
        if isinstance(choice, Choice):
            content = choice.message
        else:
            content = choice.delta
        if content.tool_calls is None:
            return None
        return [
            ToolCall(
                id=tool.id,
                type=tool.type,
                function=FunctionCall(name=tool.function.name, arguments=tool.function.arguments),
            )
            for tool in content.tool_calls
        ]

    def get_function_call_from_chat_choice(self, choice: Union[Choice, ChunkChoice]) -> Optional[FunctionCall]:
        if isinstance(choice, Choice):
            content = choice.message
        else:
            content = choice.delta
        if content.function_call is None:
            return None
        return FunctionCall(name=content.function_call.name, arguments=content.function_call.arguments)
