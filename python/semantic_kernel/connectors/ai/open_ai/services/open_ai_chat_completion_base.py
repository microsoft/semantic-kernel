# Copyright (c) Microsoft. All rights reserved.
import logging
from typing import (
    Any,
    AsyncIterable,
    Dict,
    List,
    Optional,
    Union,
)

from openai import AsyncStream
from openai.types.chat.chat_completion import ChatCompletion, Choice
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk
from openai.types.chat.chat_completion_chunk import Choice as ChunkChoice

from semantic_kernel.connectors.ai.chat_completion_client_base import (
    ChatCompletionClientBase,
)
from semantic_kernel.connectors.ai.open_ai.contents import OpenAIChatMessageContent, OpenAIStreamingChatMessageContent
from semantic_kernel.connectors.ai.open_ai.models.chat.function_call import FunctionCall
from semantic_kernel.connectors.ai.open_ai.models.chat.tool_calls import ToolCall
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_prompt_execution_settings import (
    OpenAIChatPromptExecutionSettings,
    OpenAIPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_handler import OpenAIHandler
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.models.chat.chat_role import ChatRole
from semantic_kernel.models.chat.finish_reason import FinishReason

logger: logging.Logger = logging.getLogger(__name__)


class OpenAIChatCompletionBase(OpenAIHandler, ChatCompletionClientBase):
    """OpenAI Chat completion class."""

    def get_prompt_execution_settings_class(self) -> "PromptExecutionSettings":
        """Create a request settings object."""
        return OpenAIChatPromptExecutionSettings

    async def complete_chat(
        self,
        messages: List[Dict[str, str]],
        settings: OpenAIPromptExecutionSettings,
        **kwargs,
    ) -> List[OpenAIChatMessageContent]:
        """Executes a chat completion request and returns the result.

        Arguments:
            messages {List[Dict[str,str]]} -- The messages to use for the chat completion.
            settings {OpenAIChatPromptExecutionSettings | AzureChatPromptExecutionSettings} -- The settings to use
                for the chat completion request.

        Returns:
            List[OpenAIChatMessageContent | AzureChatMessageContent] -- The completion result(s).
        """
        # TODO: replace messages with ChatHistory object with ChatMessageContent objects
        settings.messages = messages
        settings.stream = False
        if not settings.ai_model_id:
            settings.ai_model_id = self.ai_model_id
        response = await self._send_request(request_settings=settings)
        response_metadata = self._get_metadata_from_chat_response(response)
        return [self._create_chat_message_content(response, choice, response_metadata) for choice in response.choices]

    async def complete_chat_stream(
        self,
        messages: List[Dict[str, str]],
        settings: OpenAIPromptExecutionSettings,
        **kwargs,
    ) -> AsyncIterable[List[OpenAIStreamingChatMessageContent]]:
        """Executes a streaming chat completion request and returns the result.

        Arguments:
            messages {List[Tuple[str,str]]} -- The messages to use for the chat completion.
            settings {OpenAIChatPromptExecutionSettings | AzureChatPromptExecutionSettings} -- The settings to use
                for the chat completion request.

        Yields:
            List[OpenAIStreamingChatMessageContent | AzureStreamingChatMessageContent] -- A stream of
                OpenAIStreamingChatMessages or AzureStreamingChatMessageContent when using Azure.
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
            chunk_metadata = self._get_metadata_from_streaming_chat_response(chunk)
            contents = [
                self._create_streaming_chat_message_content(chunk, choice, chunk_metadata) for choice in chunk.choices
            ]
            self._update_storages(contents, update_storage)
            yield contents

    def _create_chat_message_content(
        self, response: ChatCompletion, choice: Choice, response_metadata: Dict[str, Any]
    ) -> OpenAIChatMessageContent:
        """Create a chat message content object from a choice."""
        metadata = self._get_metadata_from_chat_choice(choice)
        metadata.update(response_metadata)
        return OpenAIChatMessageContent(
            inner_content=response,
            ai_model_id=self.ai_model_id,
            metadata=metadata,
            role=ChatRole(choice.message.role),
            content=choice.message.content,
            function_call=self._get_function_call_from_chat_choice(choice),
            tool_calls=self._get_tool_calls_from_chat_choice(choice),
        )

    def _create_streaming_chat_message_content(
        self,
        chunk: ChatCompletionChunk,
        choice: ChunkChoice,
        chunk_metadata: Dict[str, Any],
    ):
        """Create a streaming chat message content object from a choice."""
        metadata = self._get_metadata_from_chat_choice(choice)
        metadata.update(chunk_metadata)
        return OpenAIStreamingChatMessageContent(
            choice_index=choice.index,
            inner_content=chunk,
            ai_model_id=self.ai_model_id,
            metadata=metadata,
            role=ChatRole(choice.delta.role),
            content=choice.delta.content,
            finish_reason=FinishReason(choice.finish_reason),
            function_call=self._get_function_call_from_chat_choice(choice),
            tool_calls=self._get_tool_calls_from_chat_choice(choice),
        )

    def _get_update_storage_fields(self) -> Dict[str, Dict[int, Any]]:
        """Get the fields to use for storing updates to the messages, tool_calls and function_calls."""
        out_messages = {}
        tool_call_ids_by_index = {}
        function_call_by_index = {}
        return {
            "out_messages": out_messages,
            "tool_call_ids_by_index": tool_call_ids_by_index,
            "function_call_by_index": function_call_by_index,
        }

    def _update_storages(
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

    def _get_metadata_from_chat_response(self, response: ChatCompletion) -> Dict[str, Any]:
        """Get metadata from a chat response."""
        return {
            "id": response.id,
            "created": response.created,
            "system_fingerprint": response.system_fingerprint,
            "usage": response.usage,
        }

    def _get_metadata_from_streaming_chat_response(self, response: ChatCompletionChunk) -> Dict[str, Any]:
        """Get metadata from a streaming chat response."""
        return {
            "id": response.id,
            "created": response.created,
            "system_fingerprint": response.system_fingerprint,
        }

    def _get_metadata_from_chat_choice(self, choice: Union[Choice, ChunkChoice]) -> Dict[str, Any]:
        """Get metadata from a chat choice."""
        return {
            "logprobs": getattr(choice, "logprobs", None),
        }

    def _get_tool_calls_from_chat_choice(self, choice: Union[Choice, ChunkChoice]) -> Optional[List[ToolCall]]:
        """Get tool calls from a chat choice."""
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

    def _get_function_call_from_chat_choice(self, choice: Union[Choice, ChunkChoice]) -> Optional[FunctionCall]:
        """Get a function call from a chat choice."""
        if isinstance(choice, Choice):
            content = choice.message
        else:
            content = choice.delta
        if content.function_call is None:
            return None
        return FunctionCall(name=content.function_call.name, arguments=content.function_call.arguments)
