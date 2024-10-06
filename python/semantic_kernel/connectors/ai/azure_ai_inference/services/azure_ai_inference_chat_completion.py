# Copyright (c) Microsoft. All rights reserved.

import logging
import sys
from collections.abc import AsyncGenerator, Callable
from typing import TYPE_CHECKING, Any, ClassVar

from semantic_kernel.connectors.ai.function_call_choice_configuration import FunctionCallChoiceConfiguration
from semantic_kernel.utils.telemetry.model_diagnostics.decorators import trace_chat_completion
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
import logging
from collections.abc import AsyncGenerator
from typing import Any

from azure.ai.inference.aio import ChatCompletionsClient
from azure.ai.inference.models import (
    AssistantMessage,
    AsyncStreamingChatCompletions,
    ChatChoice,
    ChatCompletions,
    ChatRequestMessage,
    ImageContentItem,
    ImageDetailLevel,
    ImageUrl,
    StreamingChatChoiceUpdate,
    SystemMessage,
    TextContentItem,
    ToolMessage,
    UserMessage,
)
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential
from pydantic import ValidationError

from semantic_kernel.connectors.ai.azure_ai_inference import (
    AzureAIInferenceChatPromptExecutionSettings,
    AzureAIInferenceSettings,
)
from semantic_kernel.connectors.ai.azure_ai_inference.services.azure_ai_inference_base import (
    AzureAIInferenceBase,
)
from semantic_kernel.connectors.ai.azure_ai_inference.services.utils import (
    MESSAGE_CONVERTERS,
)
from semantic_kernel.connectors.ai.chat_completion_client_base import (
    ChatCompletionClientBase,
)
from semantic_kernel.connectors.ai.function_calling_utils import (
    update_settings_from_function_call_configuration,
)
from semantic_kernel.connectors.ai.function_choice_behavior import (
    FunctionChoiceBehavior,
)
from semantic_kernel.connectors.ai.azure_ai_inference.services.azure_ai_inference_base import AzureAIInferenceBase
from semantic_kernel.connectors.ai.azure_ai_inference.services.utils import MESSAGE_CONVERTERS
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.function_calling_utils import (
    merge_function_results,
    update_settings_from_function_call_configuration,
)
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.function_calling_utils import update_settings_from_function_call_configuration
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceType
from semantic_kernel.connectors.ai.open_ai.const import DEFAULT_AZURE_API_VERSION
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ITEM_TYPES, ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.streaming_chat_message_content import (
    ITEM_TYPES as STREAMING_ITEM_TYPES,
)
from semantic_kernel.contents.streaming_chat_message_content import (
    StreamingChatMessageContent,
)
from semantic_kernel.contents.streaming_chat_message_content import ITEM_TYPES as STREAMING_ITEM_TYPES
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.image_content import ImageContent
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.streaming_text_content import StreamingTextContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.contents.utils.finish_reason import FinishReason
from semantic_kernel.exceptions.service_exceptions import (
    ServiceInitializationError,
    ServiceInvalidExecutionSettingsError,
)
from semantic_kernel.utils.experimental_decorator import experimental_class

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.prompt_execution_settings import (
        PromptExecutionSettings,
    )
    from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError
from semantic_kernel.utils.experimental_decorator import experimental_class

_MESSAGE_CONVERTER: dict[AuthorRole, Any] = {
    AuthorRole.SYSTEM: SystemMessage,
    AuthorRole.USER: UserMessage,
    AuthorRole.ASSISTANT: AssistantMessage,
    AuthorRole.TOOL: ToolMessage,
}

logger: logging.Logger = logging.getLogger(__name__)


@experimental_class
class AzureAIInferenceChatCompletion(ChatCompletionClientBase, AzureAIInferenceBase):
    """Azure AI Inference Chat Completion Service."""

    SUPPORTS_FUNCTION_CALLING: ClassVar[bool] = True

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
                raise ServiceInitializationError(
                    f"Failed to validate Azure AI Inference settings: {e}"
                ) from e

            client = ChatCompletionsClient(
                endpoint=str(azure_ai_inference_settings.endpoint),
                credential=AzureKeyCredential(
                    azure_ai_inference_settings.api_key.get_secret_value()
                ),
                user_agent=SEMANTIC_KERNEL_USER_AGENT,
                endpoint=azure_ai_inference_settings.endpoint,
                credential=AzureKeyCredential(azure_ai_inference_settings.api_key.get_secret_value()),
            )
            endpoint_to_use: str = str(azure_ai_inference_settings.endpoint)
            if azure_ai_inference_settings.api_key is not None:
                client = ChatCompletionsClient(
                    endpoint=endpoint_to_use,
                    credential=AzureKeyCredential(azure_ai_inference_settings.api_key.get_secret_value()),
                    user_agent=SEMANTIC_KERNEL_USER_AGENT,
                )
            else:
                # Try to create the client with a DefaultAzureCredential
                client = (
                    ChatCompletionsClient(
                        endpoint=endpoint_to_use,
                        credential=DefaultAzureCredential(),
                        credential_scopes=["https://cognitiveservices.azure.com/.default"],
                        api_version=DEFAULT_AZURE_API_VERSION,
                        user_agent=SEMANTIC_KERNEL_USER_AGENT,
                    ),
                )

        super().__init__(
            ai_model_id=ai_model_id,
            service_id=service_id or ai_model_id,
            client=client,
        )

    # region Overriding base class methods

    # Override from AIServiceClientBase
    @override
    def get_prompt_execution_settings_class(self) -> type["PromptExecutionSettings"]:
        return AzureAIInferenceChatPromptExecutionSettings

    @override
    @trace_chat_completion(AzureAIInferenceBase.MODEL_PROVIDER_NAME)
    async def _inner_get_chat_message_contents(
        self,
        chat_history: "ChatHistory",
        settings: "PromptExecutionSettings",
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
        settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(
            settings, AzureAIInferenceChatPromptExecutionSettings
        )  # nosec

        kernel = kwargs.get("kernel")
        if settings.function_choice_behavior is not None and (not kernel or not isinstance(kernel, Kernel)):
            raise ServiceInvalidExecutionSettingsError("Kernel is required for auto invoking functions.")

        if kernel and settings.function_choice_behavior:
            self._verify_function_choice_behavior(settings)
            self._configure_function_choice_behavior(settings, kernel)

        if (
            settings.function_choice_behavior is None
            or not settings.function_choice_behavior.auto_invoke_kernel_functions
        ):
            return await self._send_chat_request(chat_history, settings)

        kernel = kwargs.get("kernel")
        if not isinstance(kernel, Kernel):
            raise ServiceInvalidExecutionSettingsError(
                "Kernel is required for auto invoking functions."
            )

        self._verify_function_choice_behavior(settings)
        self._configure_function_choice_behavior(settings, kernel)

        for request_index in range(
            settings.function_choice_behavior.maximum_auto_invoke_attempts
        ):
            completions = await self._send_chat_request(chat_history, settings)
            chat_history.add_message(message=completions[0])
            function_calls = [
                item
                for item in chat_history.messages[-1].items
                if isinstance(item, FunctionCallContent)
            ]
        for request_index in range(settings.function_choice_behavior.maximum_auto_invoke_attempts):
            completions = await self._send_chat_request(chat_history, settings)
            function_calls = [item for item in completions[0].items if isinstance(item, FunctionCallContent)]
        for request_index in range(settings.function_choice_behavior.maximum_auto_invoke_attempts):
            completions = await self._send_chat_request(chat_history, settings)
            function_calls = [item for item in completions[0].items if isinstance(item, FunctionCallContent)]
            if (fc_count := len(function_calls)) == 0:
                return completions

            chat_history.add_message(message=completions[0])

            results = await self._invoke_function_calls(
                function_calls=function_calls,
                chat_history=chat_history,
                kernel=kernel,  # type: ignore
                arguments=kwargs.get("arguments", None),
                function_call_count=fc_count,
                request_index=request_index,
                function_behavior=settings.function_choice_behavior,
            )

            if any(result.terminate for result in results if result is not None):
                return merge_function_results(chat_history.messages[-len(results) :])
        else:
            # do a final call without auto function calling
            return await self._send_chat_request(chat_history, settings)

    async def _send_chat_request(
        self,
        chat_history: ChatHistory,
        settings: AzureAIInferenceChatPromptExecutionSettings,
    ) -> list[ChatMessageContent]:
        """Send a chat request to the Azure AI Inference service."""
    ) -> list["ChatMessageContent"]:
        if not isinstance(settings, AzureAIInferenceChatPromptExecutionSettings):
            settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(settings, AzureAIInferenceChatPromptExecutionSettings)  # nosec

        assert isinstance(self.client, ChatCompletionsClient)  # nosec
        response: ChatCompletions = await self.client.complete(
            messages=self._prepare_chat_history_for_request(chat_history),
        response: ChatCompletions = await self.client.complete(
            messages=self._format_chat_history(chat_history),
            model_extras=settings.extra_parameters,
            **settings.prepare_settings_dict(),
        )
        response_metadata = self._get_metadata_from_response(response)

        return [
            self._create_chat_message_content(response, choice, response_metadata)
            for choice in response.choices
        ]

    @override
    async def _inner_get_streaming_chat_message_contents(
        self,
        chat_history: "ChatHistory",
        settings: "PromptExecutionSettings",
    ) -> AsyncGenerator[list["StreamingChatMessageContent"], Any]:
        if not isinstance(settings, AzureAIInferenceChatPromptExecutionSettings):
            settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(settings, AzureAIInferenceChatPromptExecutionSettings)  # nosec

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

    @override
    def _verify_function_choice_settings(self, settings: "PromptExecutionSettings") -> None:
        if not isinstance(settings, AzureAIInferenceChatPromptExecutionSettings):
            raise ServiceInvalidExecutionSettingsError(
                "The settings must be an AzureAIInferenceChatPromptExecutionSettings."
            )
        if settings.extra_parameters is not None and settings.extra_parameters.get("n", 1) > 1:
            # Currently only OpenAI models allow multiple completions but the Azure AI Inference service
            # does not expose the functionality directly. If users want to have more than 1 responses, they
            # need to configure `extra_parameters` with a key of "n" and a value greater than 1.
            raise ServiceInvalidExecutionSettingsError(
                "Auto invocation of tool calls may only be used with a single completion."
            )

    @override
    def _update_function_choice_settings_callback(
        self,
    ) -> Callable[[FunctionCallChoiceConfiguration, "PromptExecutionSettings", FunctionChoiceType], None]:
        return update_settings_from_function_call_configuration

    @override
    def _reset_function_choice_settings(self, settings: "PromptExecutionSettings") -> None:
        if hasattr(settings, "tool_choice"):
            settings.tool_choice = None
        if hasattr(settings, "tools"):
            settings.tools = None

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

    # endregion

    # region Non-streaming

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
        response: AsyncStreamingChatCompletions = await self.client.complete(
            stream=True,
            messages=self._format_chat_history(chat_history),
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
                if isinstance(tool_call, ChatCompletionsFunctionToolCall):
                    items.append(
                        FunctionCallContent(
                            id=tool_call.id,
                            name=tool_call.function.name,
                            arguments=tool_call.function.arguments,
                        )
                    )
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
            finish_reason=(
                FinishReason(choice.finish_reason) if choice.finish_reason else None
            ),
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
        assert isinstance(
            settings, AzureAIInferenceChatPromptExecutionSettings
        )  # nosec

        kernel = kwargs.get("kernel")
        if settings.function_choice_behavior is not None and (not kernel or not isinstance(kernel, Kernel)):
            raise ServiceInvalidExecutionSettingsError("Kernel is required for auto invoking functions.")

        if kernel and settings.function_choice_behavior:
            self._verify_function_choice_behavior(settings)
            self._configure_function_choice_behavior(settings, kernel)

        if (
            settings.function_choice_behavior is None
            or not settings.function_choice_behavior.auto_invoke_kernel_functions
        ):
            # No auto invoke is required.
            async_generator = self._send_chat_streaming_request(chat_history, settings)
        else:
            # Auto invoke is required.
            async_generator = self._get_streaming_chat_message_contents_auto_invoke(
                chat_history, settings, **kwargs
                kernel,  # type: ignore
                kwargs.get("arguments"),
                chat_history,
                settings,
            )

        async for messages in async_generator:
            yield messages

    async def _get_streaming_chat_message_contents_auto_invoke(
        self,
        kernel: Kernel,
        arguments: KernelArguments | None,
        chat_history: ChatHistory,
        settings: AzureAIInferenceChatPromptExecutionSettings,
    ) -> AsyncGenerator[list[StreamingChatMessageContent], Any]:
        """Get streaming chat message contents from the Azure AI Inference service with auto invoking functions."""
        kernel = kwargs.get("kernel")
        if not isinstance(kernel, Kernel):
            raise ServiceInvalidExecutionSettingsError(
                "Kernel is required for auto invoking functions."
            )

        self._verify_function_choice_behavior(settings)
        self._configure_function_choice_behavior(settings, kernel)

        # mypy doesn't recognize the settings.function_choice_behavior is not None by the check above
        request_attempts = settings.function_choice_behavior.maximum_auto_invoke_attempts  # type: ignore

        for request_index in range(request_attempts):
            all_messages: list[StreamingChatMessageContent] = []
            function_call_returned = False
            async for messages in self._send_chat_streaming_request(
                chat_history, settings
            ):
                for message in messages:
                    if message:
                        all_messages.append(message)
                        if any(
                            isinstance(item, FunctionCallContent)
                            for item in message.items
                        ):
                            function_call_returned = True
                yield messages

            if not function_call_returned:
                # Response doesn't contain any function calls. No need to proceed to the next request.
                return

            full_completion: StreamingChatMessageContent = reduce(
                lambda x, y: x + y, all_messages
            )
            function_calls = [
                item
                for item in full_completion.items
                if isinstance(item, FunctionCallContent)
            ]
            chat_history.add_message(message=full_completion)

            results = await self._invoke_function_calls(
                function_calls=function_calls,
                chat_history=chat_history,
                kernel=kernel,
                arguments=arguments,
                function_call_count=len(function_calls),
                request_index=request_index,
                # mypy doesn't recognize the settings.function_choice_behavior is not None by the check above
                function_behavior=settings.function_choice_behavior,  # type: ignore
            )

            if any(result.terminate for result in results if result is not None):
                yield merge_function_results(chat_history.messages[-len(results) :])  # type: ignore
                break

    async def _send_chat_streaming_request(
        self,
        chat_history: ChatHistory,
        settings: AzureAIInferenceChatPromptExecutionSettings,
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
                self._create_streaming_chat_message_content(
                    chunk, choice, chunk_metadata
                )
                for choice in chunk.choices
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
                items.append(
                    FunctionCallContent(
                        id=tool_call.id,
                        index=choice.index,
                        name=tool_call.function.name,
                        arguments=tool_call.function.arguments,
                    )
                )

        return StreamingChatMessageContent(
            role=(
                AuthorRole(choice.delta.role)
                if choice.delta.role
                else AuthorRole.ASSISTANT
            ),
            items=items,
            choice_index=choice.index,
            inner_content=chunk,
            finish_reason=(
                FinishReason(choice.finish_reason) if choice.finish_reason else None
            ),
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

    def _get_metadata_from_response(
        self, response: ChatCompletions | StreamingChatCompletionsUpdate
    ) -> dict[str, Any]:
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

    def _verify_function_choice_behavior(
        self, settings: AzureAIInferenceChatPromptExecutionSettings
    ):
        """Verify the function choice behavior."""
        if not settings.function_choice_behavior:
            raise ServiceInvalidExecutionSettingsError(
                "Function choice behavior is required for tool calls."
            )
        if (
            settings.extra_parameters is not None
            and settings.extra_parameters.get("n", 1) > 1
        ):
        if settings.extra_parameters is not None and settings.extra_parameters.get("n", 1) > 1:
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
            raise ServiceInvalidExecutionSettingsError(
                "Function choice behavior is required for tool calls."
            )
            return
            return

        settings.function_choice_behavior.configure(
            kernel=kernel,
            update_settings_callback=update_settings_from_function_call_configuration,
            settings=settings,
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
    def _format_chat_history(self, chat_history: ChatHistory) -> list[ChatRequestMessage]:
        """Format the chat history to the expected objects for the client.

        Args:
            chat_history: The chat history.

        Returns:
            A list of formatted chat history.
        """
        chat_request_messages: list[ChatRequestMessage] = []

        for message in chat_history.messages:
            if message.role != AuthorRole.USER or not any(isinstance(item, ImageContent) for item in message.items):
                chat_request_messages.append(_MESSAGE_CONVERTER[message.role](content=message.content))
                continue

<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< main
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
<<<<<<< main
>>>>>>> main
>>>>>>> Stashed changes
            # If it's a user message and there are any image items in the message, we need to create a list of
            # content items, otherwise we need to just pass in the content as a string or it will error.
            contentItems = []
            for item in message.items:
                if isinstance(item, TextContent):
                    contentItems.append(TextContentItem(text=item.text))
                elif isinstance(item, ImageContent) and (item.data_uri or item.uri):
                    contentItems.append(
                        ImageContentItem(
                            image_url=ImageUrl(url=item.data_uri or str(item.uri), detail=ImageDetailLevel.Auto)
                        )
                    )
                else:
                    logger.warning(
                        "Unsupported item type in User message while formatting chat history for Azure AI"
                        f" Inference: {type(item)}"
                    )
            chat_request_messages.append(_MESSAGE_CONVERTER[message.role](content=contentItems))

        return chat_request_messages

    def get_prompt_execution_settings_class(
        self,
    ) -> AzureAIInferenceChatPromptExecutionSettings:
        """Get the request settings class."""
        return AzureAIInferenceChatPromptExecutionSettings
# Copyright (c) Microsoft. All rights reserved.

import logging
import sys
from collections.abc import AsyncGenerator, Callable
from typing import TYPE_CHECKING, Any, ClassVar

from semantic_kernel.connectors.ai.function_call_choice_configuration import FunctionCallChoiceConfiguration
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> ms/features/bugbash-prep
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> ms/features/bugbash-prep
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
from semantic_kernel.utils.telemetry.model_diagnostics.decorators import trace_chat_completion
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
import logging
from collections.abc import AsyncGenerator
from typing import Any

from azure.ai.inference.aio import ChatCompletionsClient
from azure.ai.inference.models import (
    AssistantMessage,
    AsyncStreamingChatCompletions,
    ChatChoice,
    ChatCompletions,
    ChatRequestMessage,
    ImageContentItem,
    ImageDetailLevel,
    ImageUrl,
    StreamingChatChoiceUpdate,
    SystemMessage,
    TextContentItem,
    ToolMessage,
    UserMessage,
)
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential
from pydantic import ValidationError

from semantic_kernel.connectors.ai.azure_ai_inference import (
    AzureAIInferenceChatPromptExecutionSettings,
    AzureAIInferenceSettings,
)
from semantic_kernel.connectors.ai.azure_ai_inference.services.azure_ai_inference_base import (
    AzureAIInferenceBase,
)
from semantic_kernel.connectors.ai.azure_ai_inference.services.utils import (
    MESSAGE_CONVERTERS,
)
from semantic_kernel.connectors.ai.chat_completion_client_base import (
    ChatCompletionClientBase,
)
from semantic_kernel.connectors.ai.function_calling_utils import (
    update_settings_from_function_call_configuration,
)
from semantic_kernel.connectors.ai.function_choice_behavior import (
    FunctionChoiceBehavior,
)
from semantic_kernel.connectors.ai.azure_ai_inference.services.azure_ai_inference_base import AzureAIInferenceBase
from semantic_kernel.connectors.ai.azure_ai_inference.services.utils import MESSAGE_CONVERTERS
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.function_calling_utils import (
    merge_function_results,
    update_settings_from_function_call_configuration,
)
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.function_calling_utils import update_settings_from_function_call_configuration
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceType
from semantic_kernel.connectors.ai.open_ai.const import DEFAULT_AZURE_API_VERSION
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ITEM_TYPES, ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.streaming_chat_message_content import (
    ITEM_TYPES as STREAMING_ITEM_TYPES,
)
from semantic_kernel.contents.streaming_chat_message_content import (
    StreamingChatMessageContent,
)
from semantic_kernel.contents.streaming_chat_message_content import ITEM_TYPES as STREAMING_ITEM_TYPES
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.image_content import ImageContent
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.streaming_text_content import StreamingTextContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.contents.utils.finish_reason import FinishReason
from semantic_kernel.exceptions.service_exceptions import (
    ServiceInitializationError,
    ServiceInvalidExecutionSettingsError,
)
from semantic_kernel.utils.experimental_decorator import experimental_class

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.prompt_execution_settings import (
        PromptExecutionSettings,
    )
    from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError
from semantic_kernel.utils.experimental_decorator import experimental_class

_MESSAGE_CONVERTER: dict[AuthorRole, Any] = {
    AuthorRole.SYSTEM: SystemMessage,
    AuthorRole.USER: UserMessage,
    AuthorRole.ASSISTANT: AssistantMessage,
    AuthorRole.TOOL: ToolMessage,
}

logger: logging.Logger = logging.getLogger(__name__)


@experimental_class
class AzureAIInferenceChatCompletion(ChatCompletionClientBase, AzureAIInferenceBase):
    """Azure AI Inference Chat Completion Service."""

    SUPPORTS_FUNCTION_CALLING: ClassVar[bool] = True

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
                raise ServiceInitializationError(
                    f"Failed to validate Azure AI Inference settings: {e}"
                ) from e

            client = ChatCompletionsClient(
                endpoint=str(azure_ai_inference_settings.endpoint),
                credential=AzureKeyCredential(
                    azure_ai_inference_settings.api_key.get_secret_value()
                ),
                user_agent=SEMANTIC_KERNEL_USER_AGENT,
                endpoint=azure_ai_inference_settings.endpoint,
                credential=AzureKeyCredential(azure_ai_inference_settings.api_key.get_secret_value()),
            )
            endpoint_to_use: str = str(azure_ai_inference_settings.endpoint)
            if azure_ai_inference_settings.api_key is not None:
                client = ChatCompletionsClient(
                    endpoint=endpoint_to_use,
                    credential=AzureKeyCredential(azure_ai_inference_settings.api_key.get_secret_value()),
                    user_agent=SEMANTIC_KERNEL_USER_AGENT,
                )
            else:
                # Try to create the client with a DefaultAzureCredential
                client = (
                    ChatCompletionsClient(
                        endpoint=endpoint_to_use,
                        credential=DefaultAzureCredential(),
                        credential_scopes=["https://cognitiveservices.azure.com/.default"],
                        api_version=DEFAULT_AZURE_API_VERSION,
                        user_agent=SEMANTIC_KERNEL_USER_AGENT,
                    ),
                )

        super().__init__(
            ai_model_id=ai_model_id,
            service_id=service_id or ai_model_id,
            client=client,
        )

<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< main
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
<<<<<<< main
>>>>>>> main
>>>>>>> Stashed changes
    # region Overriding base class methods

    # Override from AIServiceClientBase
    @override
    def get_prompt_execution_settings_class(self) -> type["PromptExecutionSettings"]:
        return AzureAIInferenceChatPromptExecutionSettings

    @override
    @trace_chat_completion(AzureAIInferenceBase.MODEL_PROVIDER_NAME)
    async def _inner_get_chat_message_contents(
        self,
        chat_history: "ChatHistory",
        settings: "PromptExecutionSettings",
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
=======
    # region Non-streaming
    @override
    @trace_chat_completion(AzureAIInferenceBase.MODEL_PROVIDER_NAME)
>>>>>>> ms/features/bugbash-prep
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
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
        settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(
            settings, AzureAIInferenceChatPromptExecutionSettings
        )  # nosec

        kernel = kwargs.get("kernel")
        if settings.function_choice_behavior is not None and (not kernel or not isinstance(kernel, Kernel)):
            raise ServiceInvalidExecutionSettingsError("Kernel is required for auto invoking functions.")

        if kernel and settings.function_choice_behavior:
            self._verify_function_choice_behavior(settings)
            self._configure_function_choice_behavior(settings, kernel)

        if (
            settings.function_choice_behavior is None
            or not settings.function_choice_behavior.auto_invoke_kernel_functions
        ):
            return await self._send_chat_request(chat_history, settings)

        kernel = kwargs.get("kernel")
        if not isinstance(kernel, Kernel):
            raise ServiceInvalidExecutionSettingsError(
                "Kernel is required for auto invoking functions."
            )

        self._verify_function_choice_behavior(settings)
        self._configure_function_choice_behavior(settings, kernel)

        for request_index in range(
            settings.function_choice_behavior.maximum_auto_invoke_attempts
        ):
            completions = await self._send_chat_request(chat_history, settings)
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< main
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
<<<<<<< main
>>>>>>> main
>>>>>>> Stashed changes
            chat_history.add_message(message=completions[0])
            function_calls = [
                item
                for item in chat_history.messages[-1].items
                if isinstance(item, FunctionCallContent)
            ]
        for request_index in range(settings.function_choice_behavior.maximum_auto_invoke_attempts):
            completions = await self._send_chat_request(chat_history, settings)
            function_calls = [item for item in completions[0].items if isinstance(item, FunctionCallContent)]
        for request_index in range(settings.function_choice_behavior.maximum_auto_invoke_attempts):
            completions = await self._send_chat_request(chat_history, settings)
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> ms/features/bugbash-prep
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> ms/features/bugbash-prep
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
            function_calls = [item for item in completions[0].items if isinstance(item, FunctionCallContent)]
            if (fc_count := len(function_calls)) == 0:
                return completions

            chat_history.add_message(message=completions[0])

            results = await self._invoke_function_calls(
                function_calls=function_calls,
                chat_history=chat_history,
                kernel=kernel,  # type: ignore
                arguments=kwargs.get("arguments", None),
                function_call_count=fc_count,
                request_index=request_index,
                function_behavior=settings.function_choice_behavior,
            )

            if any(result.terminate for result in results if result is not None):
                return merge_function_results(chat_history.messages[-len(results) :])
        else:
            # do a final call without auto function calling
            return await self._send_chat_request(chat_history, settings)

    async def _send_chat_request(
        self,
        chat_history: ChatHistory,
        settings: AzureAIInferenceChatPromptExecutionSettings,
    ) -> list[ChatMessageContent]:
        """Send a chat request to the Azure AI Inference service."""
    ) -> list["ChatMessageContent"]:
        if not isinstance(settings, AzureAIInferenceChatPromptExecutionSettings):
            settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(settings, AzureAIInferenceChatPromptExecutionSettings)  # nosec

        assert isinstance(self.client, ChatCompletionsClient)  # nosec
        response: ChatCompletions = await self.client.complete(
            messages=self._prepare_chat_history_for_request(chat_history),
        response: ChatCompletions = await self.client.complete(
            messages=self._format_chat_history(chat_history),
            model_extras=settings.extra_parameters,
            **settings.prepare_settings_dict(),
        )
        response_metadata = self._get_metadata_from_response(response)

        return [
            self._create_chat_message_content(response, choice, response_metadata)
            for choice in response.choices
        ]

    @override
    async def _inner_get_streaming_chat_message_contents(
        self,
        chat_history: "ChatHistory",
        settings: "PromptExecutionSettings",
    ) -> AsyncGenerator[list["StreamingChatMessageContent"], Any]:
        if not isinstance(settings, AzureAIInferenceChatPromptExecutionSettings):
            settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(settings, AzureAIInferenceChatPromptExecutionSettings)  # nosec

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

    @override
    def _verify_function_choice_settings(self, settings: "PromptExecutionSettings") -> None:
        if not isinstance(settings, AzureAIInferenceChatPromptExecutionSettings):
            raise ServiceInvalidExecutionSettingsError(
                "The settings must be an AzureAIInferenceChatPromptExecutionSettings."
            )
        if settings.extra_parameters is not None and settings.extra_parameters.get("n", 1) > 1:
            # Currently only OpenAI models allow multiple completions but the Azure AI Inference service
            # does not expose the functionality directly. If users want to have more than 1 responses, they
            # need to configure `extra_parameters` with a key of "n" and a value greater than 1.
            raise ServiceInvalidExecutionSettingsError(
                "Auto invocation of tool calls may only be used with a single completion."
            )

    @override
    def _update_function_choice_settings_callback(
        self,
    ) -> Callable[[FunctionCallChoiceConfiguration, "PromptExecutionSettings", FunctionChoiceType], None]:
        return update_settings_from_function_call_configuration

    @override
    def _reset_function_choice_settings(self, settings: "PromptExecutionSettings") -> None:
        if hasattr(settings, "tool_choice"):
            settings.tool_choice = None
        if hasattr(settings, "tools"):
            settings.tools = None

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

    # endregion

    # region Non-streaming

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
        response: AsyncStreamingChatCompletions = await self.client.complete(
            stream=True,
            messages=self._format_chat_history(chat_history),
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
                if isinstance(tool_call, ChatCompletionsFunctionToolCall):
                    items.append(
                        FunctionCallContent(
                            id=tool_call.id,
                            name=tool_call.function.name,
                            arguments=tool_call.function.arguments,
                        )
                    )
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
            finish_reason=(
                FinishReason(choice.finish_reason) if choice.finish_reason else None
            ),
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
        assert isinstance(
            settings, AzureAIInferenceChatPromptExecutionSettings
        )  # nosec

        kernel = kwargs.get("kernel")
        if settings.function_choice_behavior is not None and (not kernel or not isinstance(kernel, Kernel)):
            raise ServiceInvalidExecutionSettingsError("Kernel is required for auto invoking functions.")

        if kernel and settings.function_choice_behavior:
            self._verify_function_choice_behavior(settings)
            self._configure_function_choice_behavior(settings, kernel)

        if (
            settings.function_choice_behavior is None
            or not settings.function_choice_behavior.auto_invoke_kernel_functions
        ):
            # No auto invoke is required.
            async_generator = self._send_chat_streaming_request(chat_history, settings)
        else:
            # Auto invoke is required.
            async_generator = self._get_streaming_chat_message_contents_auto_invoke(
                chat_history, settings, **kwargs
                kernel,  # type: ignore
                kwargs.get("arguments"),
                chat_history,
                settings,
            )

        async for messages in async_generator:
            yield messages

    async def _get_streaming_chat_message_contents_auto_invoke(
        self,
        kernel: Kernel,
        arguments: KernelArguments | None,
        chat_history: ChatHistory,
        settings: AzureAIInferenceChatPromptExecutionSettings,
    ) -> AsyncGenerator[list[StreamingChatMessageContent], Any]:
        """Get streaming chat message contents from the Azure AI Inference service with auto invoking functions."""
        kernel = kwargs.get("kernel")
        if not isinstance(kernel, Kernel):
            raise ServiceInvalidExecutionSettingsError(
                "Kernel is required for auto invoking functions."
            )

        self._verify_function_choice_behavior(settings)
        self._configure_function_choice_behavior(settings, kernel)

        # mypy doesn't recognize the settings.function_choice_behavior is not None by the check above
        request_attempts = settings.function_choice_behavior.maximum_auto_invoke_attempts  # type: ignore

        for request_index in range(request_attempts):
            all_messages: list[StreamingChatMessageContent] = []
            function_call_returned = False
            async for messages in self._send_chat_streaming_request(
                chat_history, settings
            ):
                for message in messages:
                    if message:
                        all_messages.append(message)
                        if any(
                            isinstance(item, FunctionCallContent)
                            for item in message.items
                        ):
                            function_call_returned = True
                yield messages

            if not function_call_returned:
                # Response doesn't contain any function calls. No need to proceed to the next request.
                return

            full_completion: StreamingChatMessageContent = reduce(
                lambda x, y: x + y, all_messages
            )
            function_calls = [
                item
                for item in full_completion.items
                if isinstance(item, FunctionCallContent)
            ]
            chat_history.add_message(message=full_completion)

            results = await self._invoke_function_calls(
                function_calls=function_calls,
                chat_history=chat_history,
                kernel=kernel,
                arguments=arguments,
                function_call_count=len(function_calls),
                request_index=request_index,
                # mypy doesn't recognize the settings.function_choice_behavior is not None by the check above
                function_behavior=settings.function_choice_behavior,  # type: ignore
            )

            if any(result.terminate for result in results if result is not None):
                yield merge_function_results(chat_history.messages[-len(results) :])  # type: ignore
                break

    async def _send_chat_streaming_request(
        self,
        chat_history: ChatHistory,
        settings: AzureAIInferenceChatPromptExecutionSettings,
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
                self._create_streaming_chat_message_content(
                    chunk, choice, chunk_metadata
                )
                for choice in chunk.choices
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
                items.append(
                    FunctionCallContent(
                        id=tool_call.id,
                        index=choice.index,
                        name=tool_call.function.name,
                        arguments=tool_call.function.arguments,
                    )
                )

        return StreamingChatMessageContent(
            role=(
                AuthorRole(choice.delta.role)
                if choice.delta.role
                else AuthorRole.ASSISTANT
            ),
            items=items,
            choice_index=choice.index,
            inner_content=chunk,
            finish_reason=(
                FinishReason(choice.finish_reason) if choice.finish_reason else None
            ),
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

    def _get_metadata_from_response(
        self, response: ChatCompletions | StreamingChatCompletionsUpdate
    ) -> dict[str, Any]:
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
<<<<<<< main

    def _verify_function_choice_behavior(
        self, settings: AzureAIInferenceChatPromptExecutionSettings
    ):
        """Verify the function choice behavior."""
        if not settings.function_choice_behavior:
            raise ServiceInvalidExecutionSettingsError(
                "Function choice behavior is required for tool calls."
            )
        if (
            settings.extra_parameters is not None
            and settings.extra_parameters.get("n", 1) > 1
        ):
        if settings.extra_parameters is not None and settings.extra_parameters.get("n", 1) > 1:
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
            raise ServiceInvalidExecutionSettingsError(
                "Function choice behavior is required for tool calls."
            )
            return
            return

        settings.function_choice_behavior.configure(
            kernel=kernel,
            update_settings_callback=update_settings_from_function_call_configuration,
            settings=settings,
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
    def _format_chat_history(self, chat_history: ChatHistory) -> list[ChatRequestMessage]:
        """Format the chat history to the expected objects for the client.

        Args:
            chat_history: The chat history.

        Returns:
            A list of formatted chat history.
        """
        chat_request_messages: list[ChatRequestMessage] = []

        for message in chat_history.messages:
            if message.role != AuthorRole.USER or not any(isinstance(item, ImageContent) for item in message.items):
                chat_request_messages.append(_MESSAGE_CONVERTER[message.role](content=message.content))
                continue

            # If it's a user message and there are any image items in the message, we need to create a list of
            # content items, otherwise we need to just pass in the content as a string or it will error.
            contentItems = []
            for item in message.items:
                if isinstance(item, TextContent):
                    contentItems.append(TextContentItem(text=item.text))
                elif isinstance(item, ImageContent) and (item.data_uri or item.uri):
                    contentItems.append(
                        ImageContentItem(
                            image_url=ImageUrl(url=item.data_uri or str(item.uri), detail=ImageDetailLevel.Auto)
                        )
                    )
                else:
                    logger.warning(
                        "Unsupported item type in User message while formatting chat history for Azure AI"
                        f" Inference: {type(item)}"
                    )
            chat_request_messages.append(_MESSAGE_CONVERTER[message.role](content=contentItems))

        return chat_request_messages

    def get_prompt_execution_settings_class(
        self,
    ) -> AzureAIInferenceChatPromptExecutionSettings:
        """Get the request settings class."""
        return AzureAIInferenceChatPromptExecutionSettings
