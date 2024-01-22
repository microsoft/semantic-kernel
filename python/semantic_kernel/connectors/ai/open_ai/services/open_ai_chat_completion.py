# Copyright (c) Microsoft. All rights reserved.

import logging
from typing import (
    Any,
    Dict,
    List,
    Mapping,
    Optional,
    overload,
)

from openai import AsyncOpenAI, AsyncStream
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk
from openai.types.chat.chat_completion_chunk import Choice as ChunkChoice

from semantic_kernel.connectors.ai.ai_request_settings import AIRequestSettings
from semantic_kernel.connectors.ai.chat_completion_client_base import (
    ChatCompletionClientBase,
)
from semantic_kernel.connectors.ai.open_ai.contents import OpenAIChatMessageContent, OpenAIStreamingChatMessageContent
from semantic_kernel.connectors.ai.open_ai.request_settings.open_ai_request_settings import (
    OpenAIChatRequestSettings,
    OpenAIRequestSettings,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_config_base import (
    OpenAIConfigBase,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_handler import (
    OpenAIModelTypes,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_text_completion_base import (
    OpenAITextCompletionBase,
)
from semantic_kernel.models.contents import ChatMessageContent, StreamingChatMessageContent

logger: logging.Logger = logging.getLogger(__name__)


class OpenAIChatCompletion(OpenAIConfigBase, ChatCompletionClientBase, OpenAITextCompletionBase):
    """OpenAI Chat completion class."""

    @overload
    def __init__(
        self,
        ai_model_id: str,
        async_client: AsyncOpenAI,
        log: Optional[Any] = None,
    ) -> None:
        """
        Initialize an OpenAIChatCompletion service.

        Arguments:
            ai_model_id {str} -- OpenAI model name, see
                https://platform.openai.com/docs/models
            async_client {AsyncOpenAI} -- An existing client to use.
            log: The logger instance to use. (Optional) (Deprecated)
        """

    @overload
    def __init__(
        self,
        ai_model_id: str,
        api_key: Optional[str] = None,
        org_id: Optional[str] = None,
        default_headers: Optional[Mapping[str, str]] = None,
        log: Optional[Any] = None,
    ) -> None:
        """
        Initialize an OpenAIChatCompletion service.

        Arguments:
            ai_model_id {str} -- OpenAI model name, see
                https://platform.openai.com/docs/models
            api_key {Optional[str]} -- OpenAI API key, see
                https://platform.openai.com/account/api-keys
            org_id {Optional[str]} -- OpenAI organization ID.
                This is usually optional unless your
                account belongs to multiple organizations.
            default_headers: The default headers mapping of string keys to
                string values for HTTP requests. (Optional)
            log  -- The logger instance to use. (Optional) (Deprecated)
        """

    @overload
    def __init__(
        self,
        ai_model_id: str,
        api_key: Optional[str] = None,
        default_headers: Optional[Mapping[str, str]] = None,
        log: Optional[Any] = None,
    ) -> None:
        """
        Initialize an OpenAIChatCompletion service.

        Arguments:
            ai_model_id {str} -- OpenAI model name, see
                https://platform.openai.com/docs/models
            api_key {Optional[str]} -- OpenAI API key, see
                https://platform.openai.com/account/api-keys
            default_headers: The default headers mapping of string keys to
                string values for HTTP requests. (Optional)
            log  -- The logger instance to use. (Optional) (Deprecated)
        """

    def __init__(
        self,
        ai_model_id: str,
        api_key: Optional[str] = None,
        org_id: Optional[str] = None,
        default_headers: Optional[Mapping[str, str]] = None,
        async_client: Optional[AsyncOpenAI] = None,
        log: Optional[Any] = None,
    ) -> None:
        """
        Initialize an OpenAIChatCompletion service.

        Arguments:
            ai_model_id {str} -- OpenAI model name, see
                https://platform.openai.com/docs/models
            api_key {Optional[str]} -- OpenAI API key, see
                https://platform.openai.com/account/api-keys
            org_id {Optional[str]} -- OpenAI organization ID.
                This is usually optional unless your
                account belongs to multiple organizations.
            default_headers: The default headers mapping of string keys to
                string values for HTTP requests. (Optional)
            async_client {Optional[AsyncOpenAI]} -- An existing client to use. (Optional)
            log  -- The logger instance to use. (Optional) (Deprecated)
        """
        if log:
            logger.warning("The `log` parameter is deprecated. Please use the `logging` module instead.")
        super().__init__(
            ai_model_id=ai_model_id,
            api_key=api_key,
            org_id=org_id,
            ai_model_type=OpenAIModelTypes.CHAT,
            default_headers=default_headers,
            async_client=async_client,
        )

    @classmethod
    def from_dict(cls, settings: Dict[str, str]) -> "OpenAIChatCompletion":
        """
        Initialize an Open AI service from a dictionary of settings.

        Arguments:
            settings: A dictionary of settings for the service.
        """

        return OpenAIChatCompletion(
            ai_model_id=settings["ai_model_id"],
            api_key=settings["api_key"],
            org_id=settings.get("org_id"),
            default_headers=settings.get("default_headers"),
        )

    async def complete_chat(
        self,
        messages: List[Dict[str, str]],
        settings: OpenAIRequestSettings,
        **kwargs,
    ) -> List[ChatMessageContent]:
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
        if settings.ai_model_id is None:
            settings.ai_model_id = self.ai_model_id
        response = await self._send_request(request_settings=settings)
        response_metadata = self.get_metadata_from_chat_response(response)
        return [self._create_return_content(response, choice, response_metadata) for choice in response.choices]

    def _create_return_content(self, response, choice, response_metadata):
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

    async def complete_chat_stream(
        self,
        messages: List[Dict[str, str]],
        settings: OpenAIRequestSettings,
        **kwargs,
    ) -> List[StreamingChatMessageContent]:
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
        if settings.ai_model_id is None:
            settings.ai_model_id = self.ai_model_id
        response = await self._send_request(request_settings=settings)
        if not isinstance(response, AsyncStream):
            raise ValueError("Expected an AsyncStream[ChatCompletionChunk] response.")

        out_messages = {}
        tool_call_ids_by_index = {}
        function_call_by_index = {}

        async for chunk in response:
            if len(chunk.choices) == 0:
                continue
            chunk_metadata = self.get_metadata_from_streaming_chat_response(chunk)
            contents = [self._create_return_content_stream(chunk, choice, chunk_metadata) for choice in chunk.choices]
            self._handle_updates(contents, out_messages, tool_call_ids_by_index, function_call_by_index)
            yield contents

    def _create_return_content_stream(
        self,
        chunk: ChatCompletionChunk,
        choice: ChunkChoice,
        chunk_metadata: Dict[str, Any],
    ):
        metadata = self.get_metadata_from_chat_choice(choice)
        metadata.update(chunk_metadata)
        return OpenAIStreamingChatMessageContent(
            inner_content=chunk,
            ai_model_id=self.ai_model_id,
            metadata=metadata,
            role=choice.delta.role,
            content=choice.delta.content,
            finish_reason=choice.finish_reason,
            function_call=self.get_function_call_from_chat_choice(choice),
            tool_calls=self.get_tool_calls_from_chat_choice(choice),
        )

    def _handle_updates(self, contents, out_messages, tool_call_ids_by_index, function_call_by_index):
        """Handle updates to the messages, tool_calls and function_calls.

        This will be used for auto-invoking tools.
        """
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

    def get_request_settings_class(self) -> "AIRequestSettings":
        """Create a request settings object."""
        return OpenAIChatRequestSettings
