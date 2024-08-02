# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
import sys
from collections.abc import AsyncGenerator
from functools import reduce
from typing import TYPE_CHECKING, Any

from semantic_kernel.utils.telemetry.user_agent import SEMANTIC_KERNEL_USER_AGENT

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from azure.ai.inference.aio import ChatCompletionsClient
from azure.ai.inference.models import (
    AsyncStreamingChatCompletions,
    ChatChoice,
    ChatCompletions,
    ChatCompletionsFunctionToolCall,
    ChatRequestMessage,
    StreamingChatChoiceUpdate,
    StreamingChatCompletionsUpdate,
)
from azure.core.credentials import AzureKeyCredential
from pydantic import ValidationError

from semantic_kernel.connectors.ai.azure_ai_inference import (
    AzureAIInferenceChatPromptExecutionSettings,
    AzureAIInferenceSettings,
)
from semantic_kernel.connectors.ai.azure_ai_inference.services.azure_ai_inference_base import AzureAIInferenceBase
from semantic_kernel.connectors.ai.azure_ai_inference.services.utils import MESSAGE_CONVERTERS
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.function_calling_utils import update_settings_from_function_call_configuration
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ITEM_TYPES, ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.streaming_chat_message_content import ITEM_TYPES as STREAMING_ITEM_TYPES
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.streaming_text_content import StreamingTextContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.contents.utils.finish_reason import FinishReason
from semantic_kernel.exceptions.service_exceptions import (
    ServiceInitializationError,
    ServiceInvalidExecutionSettingsError,
)
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.kernel import Kernel
from semantic_kernel.utils.experimental_decorator import experimental_class

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings

logger: logging.Logger = logging.getLogger(__name__)


@experimental_class
class AzureAIInferenceChatCompletion(ChatCompletionClientBase, AzureAIInferenceBase):
    """Azure AI Inference Chat Completion Service."""

    def __init__(
        self,
        ai_model_id: str,
        api_key: str | None = None,
        endpoint: str | None = None,
        service_id: str | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
        client: ChatCompletionsClient | None = None,
    ) -> None:
        """Initialize the Azure AI Inference Chat Completion service.

        If no arguments are provided, the service will attempt to load the settings from the environment.
        The following environment variables are used:
        - AZURE_AI_INFERENCE_API_KEY
        - AZURE_AI_INFERENCE_ENDPOINT

        Args:
            ai_model_id: (str): A string that is used to identify the model such as the model name. (Required)
            api_key (str | None): The API key for the Azure AI Inference service deployment. (Optional)
            endpoint (str | None): The endpoint of the Azure AI Inference service deployment. (Optional)
            service_id (str | None): Service ID for the chat completion service. (Optional)
            env_file_path (str | None): The path to the environment file. (Optional)
            env_file_encoding (str | None): The encoding of the environment file. (Optional)
            client (ChatCompletionsClient | None): The Azure AI Inference client to use. (Optional)

        Raises:
            ServiceInitializationError: If an error occurs during initialization.
        """
        if not client:
            try:
                azure_ai_inference_settings = AzureAIInferenceSettings.create(
                    api_key=api_key,
                    endpoint=endpoint,
                    env_file_path=env_file_path,
                    env_file_encoding=env_file_encoding,
                )
            except ValidationError as e:
                raise ServiceInitializationError(f"Failed to validate Azure AI Inference settings: {e}") from e

            client = ChatCompletionsClient(
                endpoint=str(azure_ai_inference_settings.endpoint),
                credential=AzureKeyCredential(azure_ai_inference_settings.api_key.get_secret_value()),
                user_agent=SEMANTIC_KERNEL_USER_AGENT,
            )

        super().__init__(
            ai_model_id=ai_model_id,
            service_id=service_id or ai_model_id,
            client=client,
        )

    # region Non-streaming
    async def get_chat_message_contents(
        self,
        chat_history: ChatHistory,
        settings: "PromptExecutionSettings",
        **kwargs: Any,
    ) -> list[ChatMessageContent]:
        """Get chat message contents from the Azure AI Inference service.

        Args:
            chat_history: A list of chats in a chat_history object.
            settings: Settings for the request.
            kwargs: Optional arguments.

        Returns:
            A list of chat message contents.
        """
        settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(settings, AzureAIInferenceChatPromptExecutionSettings)  # nosec

        if (
            settings.function_choice_behavior is None
            or not settings.function_choice_behavior.auto_invoke_kernel_functions
        ):
            return await self._send_chat_request(chat_history, settings)

        kernel = kwargs.get("kernel")
        if not isinstance(kernel, Kernel):
            raise ServiceInvalidExecutionSettingsError("Kernel is required for auto invoking functions.")

        self._verify_function_choice_behavior(settings)
        self._configure_function_choice_behavior(settings, kernel)

        for request_index in range(settings.function_choice_behavior.maximum_auto_invoke_attempts):
            completions = await self._send_chat_request(chat_history, settings)
            chat_history.add_message(message=completions[0])
            function_calls = [item for item in chat_history.messages[-1].items if isinstance(item, FunctionCallContent)]
            if (fc_count := len(function_calls)) == 0:
                return completions

            results = await self._invoke_function_calls(
                function_calls=function_calls,
                chat_history=chat_history,
                kernel=kernel,
                arguments=kwargs.get("arguments", None),
                function_call_count=fc_count,
                request_index=request_index,
                function_behavior=settings.function_choice_behavior,
            )

            if any(result.terminate for result in results if result is not None):
                return completions
        else:
            # do a final call without auto function calling
            return await self._send_chat_request(chat_history, settings)

    async def _send_chat_request(
        self, chat_history: ChatHistory, settings: AzureAIInferenceChatPromptExecutionSettings
    ) -> list[ChatMessageContent]:
        """Send a chat request to the Azure AI Inference service."""
        assert isinstance(self.client, ChatCompletionsClient)  # nosec
        response: ChatCompletions = await self.client.complete(
            messages=self._prepare_chat_history_for_request(chat_history),
            model_extras=settings.extra_parameters,
            **settings.prepare_settings_dict(),
        )
        response_metadata = self._get_metadata_from_response(response)

        return [self._create_chat_message_content(response, choice, response_metadata) for choice in response.choices]

    def _create_chat_message_content(
        self, response: ChatCompletions, choice: ChatChoice, metadata: dict[str, Any]
    ) -> ChatMessageContent:
        """Create a chat message content object.

        Args:
            response: The response from the service.
            choice: The choice from the response.
            metadata: The metadata from the response.

        Returns:
            A chat message content object.
        """
        items: list[ITEM_TYPES] = []
        if choice.message.content:
            items.append(
                TextContent(
                    text=choice.message.content,
                    inner_content=response,
                    metadata=metadata,
                )
            )
        if choice.message.tool_calls:
            for tool_call in choice.message.tool_calls:
                if isinstance(tool_call, ChatCompletionsFunctionToolCall):
                    items.append(
                        FunctionCallContent(
                            id=tool_call.id,
                            name=tool_call.function.name,
                            arguments=tool_call.function.arguments,
                        )
                    )

        return ChatMessageContent(
            role=AuthorRole(choice.message.role),
            items=items,
            inner_content=response,
            finish_reason=FinishReason(choice.finish_reason) if choice.finish_reason else None,
            metadata=metadata,
        )

    # endregion

    # region Streaming
    async def get_streaming_chat_message_contents(
        self,
        chat_history: ChatHistory,
        settings: "PromptExecutionSettings",
        **kwargs: Any,
    ) -> AsyncGenerator[list[StreamingChatMessageContent], Any]:
        """Get streaming chat message contents from the Azure AI Inference service.

        Args:
            chat_history: A list of chats in a chat_history object.
            settings: Settings for the request.
            kwargs: Optional arguments.

        Returns:
            A list of chat message contents.
        """
        settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(settings, AzureAIInferenceChatPromptExecutionSettings)  # nosec

        if (
            settings.function_choice_behavior is None
            or not settings.function_choice_behavior.auto_invoke_kernel_functions
        ):
            # No auto invoke is required.
            async_generator = self._send_chat_streaming_request(chat_history, settings)
        else:
            # Auto invoke is required.
            async_generator = self._get_streaming_chat_message_contents_auto_invoke(chat_history, settings, **kwargs)

        async for messages in async_generator:
            yield messages

    async def _get_streaming_chat_message_contents_auto_invoke(
        self,
        chat_history: ChatHistory,
        settings: AzureAIInferenceChatPromptExecutionSettings,
        **kwargs: Any,
    ) -> AsyncGenerator[list[StreamingChatMessageContent], Any]:
        """Get streaming chat message contents from the Azure AI Inference service with auto invoking functions."""
        kernel = kwargs.get("kernel")
        if not isinstance(kernel, Kernel):
            raise ServiceInvalidExecutionSettingsError("Kernel is required for auto invoking functions.")

        self._verify_function_choice_behavior(settings)
        self._configure_function_choice_behavior(settings, kernel)

        # mypy doesn't recognize the settings.function_choice_behavior is not None by the check above
        request_attempts = settings.function_choice_behavior.maximum_auto_invoke_attempts  # type: ignore

        for request_index in range(request_attempts):
            all_messages: list[StreamingChatMessageContent] = []
            function_call_returned = False
            async for messages in self._send_chat_streaming_request(chat_history, settings):
                for message in messages:
                    if message:
                        all_messages.append(message)
                        if any(isinstance(item, FunctionCallContent) for item in message.items):
                            function_call_returned = True
                yield messages

            if not function_call_returned:
                # Response doesn't contain any function calls. No need to proceed to the next request.
                return

            full_completion: StreamingChatMessageContent = reduce(lambda x, y: x + y, all_messages)
            function_calls = [item for item in full_completion.items if isinstance(item, FunctionCallContent)]
            chat_history.add_message(message=full_completion)

            results = await self._invoke_function_calls(
                function_calls=function_calls,
                chat_history=chat_history,
                kernel=kernel,
                arguments=kwargs.get("arguments", None),
                function_call_count=len(function_calls),
                request_index=request_index,
                # mypy doesn't recognize the settings.function_choice_behavior is not None by the check above
                function_behavior=settings.function_choice_behavior,  # type: ignore
            )

            if any(result.terminate for result in results if result is not None):
                return

    async def _send_chat_streaming_request(
        self, chat_history: ChatHistory, settings: AzureAIInferenceChatPromptExecutionSettings
    ) -> AsyncGenerator[list[StreamingChatMessageContent], Any]:
        """Send a streaming chat request to the Azure AI Inference service."""
        assert isinstance(self.client, ChatCompletionsClient)  # nosec
        response: AsyncStreamingChatCompletions = await self.client.complete(
            stream=True,
            messages=self._prepare_chat_history_for_request(chat_history),
            model_extras=settings.extra_parameters,
            **settings.prepare_settings_dict(),
        )

        async for chunk in response:
            if len(chunk.choices) == 0:
                continue
            chunk_metadata = self._get_metadata_from_response(chunk)
            yield [
                self._create_streaming_chat_message_content(chunk, choice, chunk_metadata) for choice in chunk.choices
            ]

    def _create_streaming_chat_message_content(
        self,
        chunk: AsyncStreamingChatCompletions,
        choice: StreamingChatChoiceUpdate,
        metadata: dict[str, Any],
    ) -> StreamingChatMessageContent:
        """Create a streaming chat message content object.

        Args:
            chunk: The chunk from the response.
            choice: The choice from the response.
            metadata: The metadata from the response.

        Returns:
            A streaming chat message content object.
        """
        items: list[STREAMING_ITEM_TYPES] = []
        if choice.delta.content:
            items.append(
                StreamingTextContent(
                    choice_index=choice.index,
                    text=choice.delta.content,
                    inner_content=chunk,
                    metadata=metadata,
                )
            )
        if choice.delta.tool_calls:
            for tool_call in choice.delta.tool_calls:
                if isinstance(tool_call, ChatCompletionsFunctionToolCall):
                    items.append(
                        FunctionCallContent(
                            id=tool_call.id,
                            index=choice.index,
                            name=tool_call.function.name,
                            arguments=tool_call.function.arguments,
                        )
                    )

        return StreamingChatMessageContent(
            role=AuthorRole(choice.delta.role) if choice.delta.role else AuthorRole.ASSISTANT,
            items=items,
            choice_index=choice.index,
            inner_content=chunk,
            finish_reason=FinishReason(choice.finish_reason) if choice.finish_reason else None,
            metadata=metadata,
        )

    # endregion

    @override
    def _prepare_chat_history_for_request(
        self,
        chat_history: ChatHistory,
        role_key: str = "role",
        content_key: str = "content",
    ) -> list[ChatRequestMessage]:
        chat_request_messages: list[ChatRequestMessage] = []

        for message in chat_history.messages:
            chat_request_messages.append(MESSAGE_CONVERTERS[message.role](message))

        return chat_request_messages

    def _get_metadata_from_response(self, response: ChatCompletions | StreamingChatCompletionsUpdate) -> dict[str, Any]:
        """Get metadata from the response.

        Args:
            response: The response from the service.

        Returns:
            A dictionary containing metadata.
        """
        return {
            "id": response.id,
            "model": response.model,
            "created": response.created,
            "usage": response.usage,
        }

    def _verify_function_choice_behavior(self, settings: AzureAIInferenceChatPromptExecutionSettings):
        """Verify the function choice behavior."""
        if not settings.function_choice_behavior:
            raise ServiceInvalidExecutionSettingsError("Function choice behavior is required for tool calls.")
        if settings.extra_parameters is not None and settings.extra_parameters.get("n", 1) > 1:
            # Currently only OpenAI models allow multiple completions but the Azure AI Inference service
            # does not expose the functionality directly. If users want to have more than 1 responses, they
            # need to configure `extra_parameters` with a key of "n" and a value greater than 1.
            raise ServiceInvalidExecutionSettingsError(
                "Auto invocation of tool calls may only be used with a single completion."
            )

    def _configure_function_choice_behavior(
        self, settings: AzureAIInferenceChatPromptExecutionSettings, kernel: Kernel
    ):
        """Configure the function choice behavior to include the kernel functions."""
        if not settings.function_choice_behavior:
            raise ServiceInvalidExecutionSettingsError("Function choice behavior is required for tool calls.")

        settings.function_choice_behavior.configure(
            kernel=kernel, update_settings_callback=update_settings_from_function_call_configuration, settings=settings
        )

    async def _invoke_function_calls(
        self,
        function_calls: list[FunctionCallContent],
        chat_history: ChatHistory,
        kernel: Kernel,
        arguments: KernelArguments | None,
        function_call_count: int,
        request_index: int,
        function_behavior: FunctionChoiceBehavior,
    ):
        """Invoke function calls."""
        logger.info(f"processing {function_call_count} tool calls in parallel.")

        return await asyncio.gather(
            *[
                kernel.invoke_function_call(
                    function_call=function_call,
                    chat_history=chat_history,
                    arguments=arguments,
                    function_call_count=function_call_count,
                    request_index=request_index,
                    function_behavior=function_behavior,
                )
                for function_call in function_calls
            ],
        )

    @override
    def get_prompt_execution_settings_class(
        self,
    ) -> type["PromptExecutionSettings"]:
        """Get the request settings class."""
        return AzureAIInferenceChatPromptExecutionSettings
