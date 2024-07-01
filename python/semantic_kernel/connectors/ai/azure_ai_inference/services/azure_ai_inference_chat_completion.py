# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
from collections.abc import AsyncGenerator
from functools import reduce
from typing import Any

from azure.ai.inference.aio import ChatCompletionsClient
from azure.ai.inference.models import (
    AsyncStreamingChatCompletions,
    ChatChoice,
    ChatCompletions,
    ChatCompletionsFunctionToolCall,
    StreamingChatChoiceUpdate,
)
from azure.core.credentials import AzureKeyCredential
from pydantic import ValidationError

from semantic_kernel.connectors.ai.azure_ai_inference import (
    AzureAIInferenceChatPromptExecutionSettings,
    AzureAIInferenceSettings,
)
from semantic_kernel.connectors.ai.azure_ai_inference.services.azure_ai_inference_base import AzureAIInferenceBase
from semantic_kernel.connectors.ai.azure_ai_inference.services.azure_ai_inference_conversion_utils import (
    format_chat_history,
)
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.function_calling_utils import kernel_function_metadata_to_function_call_format
from semantic_kernel.connectors.ai.function_choice_behavior import (
    FunctionCallChoiceConfiguration,
    FunctionChoiceBehavior,
)
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
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
                endpoint=azure_ai_inference_settings.endpoint,
                credential=AzureKeyCredential(azure_ai_inference_settings.api_key.get_secret_value()),
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
        settings: AzureAIInferenceChatPromptExecutionSettings,
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
        if (
            settings.function_choice_behavior is None
            or not settings.function_choice_behavior.auto_invoke_kernel_functions
        ):
            return await self._send_chat_request(chat_history, settings)

        self._verify_function_choice_behavior(settings, **kwargs)
        kernel: Kernel = kwargs.get("kernel")
        arguments: KernelArguments = kwargs.get("arguments")
        self._configure_function_choice_behavior(settings, kernel)

        for request_index in range(settings.function_choice_behavior.maximum_auto_invoke_attempts):
            completions = await self._send_chat_request(chat_history, settings)
            # TODO(<TaoChen>): make sure there is only one message.
            # Currently only OpenAI models allow multiple messages but the Azure AI Inference service
            # requires a special handling for multiple messages.
            chat_history.add_message(message=completions[0])
            function_calls = [item for item in chat_history.messages[-1].items if isinstance(item, FunctionCallContent)]
            if (fc_count := len(function_calls)) == 0:
                return completions

            results = await self._process_function_calls(
                function_calls=function_calls,
                chat_history=chat_history,
                kernel=kernel,
                arguments=arguments,
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
        response: ChatCompletions = await self.client.complete(
            messages=format_chat_history(chat_history),
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
        items = []
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
        settings: AzureAIInferenceChatPromptExecutionSettings,
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
        self._verify_function_choice_behavior(settings, **kwargs)
        kernel: Kernel = kwargs.get("kernel")
        arguments: KernelArguments = kwargs.get("arguments")
        self._configure_function_choice_behavior(settings, kernel)
        request_attempts = settings.function_choice_behavior.maximum_auto_invoke_attempts

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

            results = await self._process_function_calls(
                function_calls=function_calls,
                chat_history=chat_history,
                kernel=kernel,
                arguments=arguments,
                function_call_count=len(function_calls),
                request_index=request_index,
                function_behavior=settings.function_choice_behavior,
            )

            if any(result.terminate for result in results if result is not None):
                return

    async def _send_chat_streaming_request(
        self, chat_history: ChatHistory, settings: AzureAIInferenceChatPromptExecutionSettings
    ) -> AsyncGenerator[list[StreamingChatMessageContent], Any]:
        """Send a streaming chat request to the Azure AI Inference service."""
        response: AsyncStreamingChatCompletions = await self.client.complete(
            stream=True,
            messages=format_chat_history(chat_history),
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
        items = []
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

    def _get_metadata_from_response(self, response: ChatCompletions | AsyncStreamingChatCompletions) -> dict[str, Any]:
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

    def _verify_function_choice_behavior(self, settings: AzureAIInferenceChatPromptExecutionSettings, **kwargs: Any):
        """Verify the function choice behavior."""
        kernel = kwargs.get("kernel", None)
        arguments = kwargs.get("arguments", None)

        if settings.function_choice_behavior is not None:
            if kernel is None:
                raise ServiceInvalidExecutionSettingsError("Kernel is required for tool calls.")
            if arguments is None and settings.function_choice_behavior.auto_invoke_kernel_functions:
                raise ServiceInvalidExecutionSettingsError("Kernel arguments are required for auto tool calls.")

    def _configure_function_choice_behavior(
        self, settings: AzureAIInferenceChatPromptExecutionSettings, kernel: Kernel
    ):
        """Configure the function choice behavior to include the kernel functions."""

        def _config_call_back(
            function_choice_configuration: FunctionCallChoiceConfiguration,
            settings: AzureAIInferenceChatPromptExecutionSettings,
            type: str,
        ):
            """Update the settings from a FunctionChoiceConfiguration."""
            if function_choice_configuration.available_functions:
                settings.tool_choice = type
                # The list of tool objects will be initialized with the JSON string returned by
                # `kernel_function_metadata_to_function_call_format`.
                settings.tools = [
                    kernel_function_metadata_to_function_call_format(f)
                    for f in function_choice_configuration.available_functions
                ]

        settings.function_choice_behavior.configure(
            kernel=kernel, update_settings_callback=_config_call_back, settings=settings
        )

    async def _process_function_calls(
        self,
        function_calls: list[FunctionCallContent],
        chat_history: ChatHistory,
        kernel: Kernel,
        arguments: KernelArguments,
        function_call_count: int,
        request_index: int,
        function_behavior: FunctionChoiceBehavior,
    ):
        """Process function calls."""
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

    def get_prompt_execution_settings_class(
        self,
    ) -> AzureAIInferenceChatPromptExecutionSettings:
        """Get the request settings class."""
        return AzureAIInferenceChatPromptExecutionSettings
