# Copyright (c) Microsoft. All rights reserved.

<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
import logging
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
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
import logging
<<<<<<< Updated upstream
=======
import json
import logging
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
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
import json
import logging
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
import json
import logging
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> head
import sys
from collections.abc import AsyncGenerator
from typing import Any, ClassVar

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
from collections.abc import AsyncGenerator
from typing import Any
>>>>>>> Stashed changes

from anthropic import AsyncAnthropic
from anthropic.types import (
    ContentBlockStopEvent,
    Message,
    RawContentBlockDeltaEvent,
    RawMessageDeltaEvent,
    RawMessageStartEvent,
    TextBlock,
<<<<<<< Updated upstream
<<<<<<< Updated upstream
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
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
=======
<<<<<<< Updated upstream
=======
<<<<<<< div
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
>>>>>>> head
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
from collections.abc import AsyncGenerator
from typing import Any
import sys
from collections.abc import AsyncGenerator
from typing import Any, ClassVar

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from anthropic import AsyncAnthropic
from anthropic.lib.streaming._types import TextEvent
from anthropic.types import (
    ContentBlockStopEvent,
    Message,
    RawMessageDeltaEvent,
    RawMessageStartEvent,
    TextBlock,
    ToolUseBlock,
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
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
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
)
from pydantic import ValidationError

from semantic_kernel.connectors.ai.anthropic.prompt_execution_settings.anthropic_prompt_execution_settings import (
    AnthropicChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.anthropic.settings.anthropic_settings import AnthropicSettings
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ITEM_TYPES, ChatMessageContent
=======
=======
>>>>>>> Stashed changes
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
>>>>>>> Stashed changes
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ITEM_TYPES, ChatMessageContent
=======
<<<<<<< div
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
from semantic_kernel.connectors.ai.function_call_choice_configuration import FunctionCallChoiceConfiguration
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceType
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ITEM_TYPES, ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
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
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
from semantic_kernel.contents.streaming_chat_message_content import ITEM_TYPES as STREAMING_ITEM_TYPES
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.streaming_text_content import StreamingTextContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.contents.utils.finish_reason import FinishReason as SemanticKernelFinishReason
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError, ServiceResponseException
from semantic_kernel.utils.experimental_decorator import experimental_class
from semantic_kernel.utils.telemetry.model_diagnostics.decorators import trace_chat_completion
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< Updated upstream
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
=======
=======
<<<<<<< div
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
>>>>>>> head
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError, ServiceResponseException
from semantic_kernel.exceptions.service_exceptions import (
    ServiceInitializationError,
    ServiceInvalidResponseError,
    ServiceResponseException,
)
from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata
from semantic_kernel.utils.experimental_decorator import experimental_class
from semantic_kernel.utils.telemetry.model_diagnostics.decorators import trace_chat_completion
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
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
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
from semantic_kernel.exceptions.service_exceptions import (
    ServiceInitializationError,
    ServiceResponseException,
)
from semantic_kernel.utils.experimental_decorator import experimental_class
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
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
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError, ServiceResponseException
from semantic_kernel.utils.experimental_decorator import experimental_class
from semantic_kernel.utils.telemetry.model_diagnostics.decorators import trace_chat_completion
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
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
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError, ServiceResponseException
from semantic_kernel.utils.experimental_decorator import experimental_class
from semantic_kernel.utils.telemetry.model_diagnostics.decorators import trace_chat_completion
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError, ServiceResponseException
from semantic_kernel.utils.experimental_decorator import experimental_class
from semantic_kernel.utils.telemetry.model_diagnostics.decorators import trace_chat_completion
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> head

# map finish reasons from Anthropic to Semantic Kernel
ANTHROPIC_TO_SEMANTIC_KERNEL_FINISH_REASON_MAP = {
    "end_turn": SemanticKernelFinishReason.STOP,
    "max_tokens": SemanticKernelFinishReason.LENGTH,
    "tool_use": SemanticKernelFinishReason.TOOL_CALLS,
}

logger: logging.Logger = logging.getLogger(__name__)


@experimental_class
class AnthropicChatCompletion(ChatCompletionClientBase):
    """Antropic ChatCompletion class."""

<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
    MODEL_PROVIDER_NAME: ClassVar[str] = "anthropic"
    SUPPORTS_FUNCTION_CALLING: ClassVar[bool] = False

    async_client: AsyncAnthropic

=======
    MODEL_PROVIDER_NAME: ClassVar[str] = "anthropic"
    SUPPORTS_FUNCTION_CALLING: ClassVar[bool] = False

    async_client: AsyncAnthropic

>>>>>>> Stashed changes
=======
    async_client: AsyncAnthropic
    
>>>>>>> Stashed changes
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< Updated upstream
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> head
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    MODEL_PROVIDER_NAME: ClassVar[str] = "anthropic"
    SUPPORTS_FUNCTION_CALLING: ClassVar[bool] = True

    async_client: AsyncAnthropic

    async_client: AsyncAnthropic
    
    MODEL_PROVIDER_NAME: ClassVar[str] = "anthropic"

    async_client: AsyncAnthropic

<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
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
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
    def __init__(
        self,
        ai_model_id: str | None = None,
        service_id: str | None = None,
        api_key: str | None = None,
        async_client: AsyncAnthropic | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
    ) -> None:
        """Initialize an AnthropicChatCompletion service.

        Args:
            ai_model_id: Anthropic model name, see
                https://docs.anthropic.com/en/docs/about-claude/models#model-names
            service_id: Service ID tied to the execution settings.
            api_key: The optional API key to use. If provided will override,
                the env vars or .env file value.
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
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
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
<<<<<<< Updated upstream
=======
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
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
            async_client: An existing client to use.
            env_file_path: Use the environment settings file as a fallback
                to environment variables.
            env_file_encoding: The encoding of the environment settings file.
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
=======
>>>>>>> Stashed changes
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
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
            async_client: An existing client to use. 
            env_file_path: Use the environment settings file as a fallback
                to environment variables. 
            env_file_encoding: The encoding of the environment settings file. 
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
            async_client: An existing client to use.
            env_file_path: Use the environment settings file as a fallback
                to environment variables.
            env_file_encoding: The encoding of the environment settings file.
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
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
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
        """
        try:
            anthropic_settings = AnthropicSettings.create(
                api_key=api_key,
                chat_model_id=ai_model_id,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as ex:
            raise ServiceInitializationError("Failed to create Anthropic settings.", ex) from ex
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
<<<<<<< Updated upstream

=======
        
>>>>>>> Stashed changes
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
=======
<<<<<<< HEAD
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes

=======
        
>>>>>>> Stashed changes
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

        

>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
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
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======

        

>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> head
        if not anthropic_settings.chat_model_id:
            raise ServiceInitializationError("The Anthropic chat model ID is required.")

        if not async_client:
            async_client = AsyncAnthropic(
                api_key=anthropic_settings.api_key.get_secret_value(),
            )

        super().__init__(
            async_client=async_client,
            service_id=service_id or anthropic_settings.chat_model_id,
            ai_model_id=anthropic_settings.chat_model_id,
        )

<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
<<<<<<< Updated upstream
    @override
    @trace_chat_completion(MODEL_PROVIDER_NAME)
=======
>>>>>>> Stashed changes
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
=======
<<<<<<< Updated upstream
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
>>>>>>> Stashed changes
>>>>>>> head
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    @override
    @trace_chat_completion(MODEL_PROVIDER_NAME)
    @override
    @trace_chat_completion(MODEL_PROVIDER_NAME)
<<<<<<< div
=======
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
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
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
    async def get_chat_message_contents(
        self,
        chat_history: "ChatHistory",
        settings: "PromptExecutionSettings",
        **kwargs: Any,
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
    ) -> list["ChatMessageContent"]:
=======
    ) -> list["ChatMessageContent"]: 
>>>>>>> Stashed changes
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
=======
=======
<<<<<<< main
<<<<<<< Updated upstream
    @override
    @trace_chat_completion(MODEL_PROVIDER_NAME)
=======
>>>>>>> Stashed changes
=======
    @override
    @trace_chat_completion(MODEL_PROVIDER_NAME)
    @override
    @trace_chat_completion(MODEL_PROVIDER_NAME)
>>>>>>> main
    async def get_chat_message_contents(
        self,
        chat_history: "ChatHistory",
        settings: "PromptExecutionSettings",
        **kwargs: Any,
<<<<<<< HEAD
<<<<<<< Updated upstream
    ) -> list["ChatMessageContent"]:
=======
    ) -> list["ChatMessageContent"]: 
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
    ) -> list["ChatMessageContent"]:
    ) -> list["ChatMessageContent"]: 
    ) -> list["ChatMessageContent"]:
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
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
    ) -> list["ChatMessageContent"]:
    ) -> list["ChatMessageContent"]: 
    ) -> list["ChatMessageContent"]:
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
    ) -> list["ChatMessageContent"]:
    ) -> list["ChatMessageContent"]: 
    ) -> list["ChatMessageContent"]:
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> head
        """Executes a chat completion request and returns the result.

        Args:
            chat_history: The chat history to use for the chat completion.
            settings: The settings to use for the chat completion request.
            kwargs: The optional arguments.

        Returns:
            The completion result(s).
        """
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
=======
>>>>>>> Stashed changes
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
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
    # region Overriding base class methods

    # Override from AIServiceClientBase
    @override
    def get_prompt_execution_settings_class(self) -> type["PromptExecutionSettings"]:
        return AnthropicChatPromptExecutionSettings

    @override
    @trace_chat_completion(MODEL_PROVIDER_NAME)
    async def _inner_get_chat_message_contents(
        self,
        chat_history: "ChatHistory",
        settings: "PromptExecutionSettings",
    ) -> list["ChatMessageContent"]:
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> upstream/main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
>>>>>>> upstream/main
=======
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
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> upstream/main
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> upstream/main
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
        if not isinstance(settings, AnthropicChatPromptExecutionSettings):
            settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(settings, AnthropicChatPromptExecutionSettings)  # nosec

        settings.ai_model_id = settings.ai_model_id or self.ai_model_id
        settings.messages = self._prepare_chat_history_for_request(chat_history)
        try:
            response = await self.async_client.messages.create(**settings.prepare_settings_dict())
        except Exception as ex:
            raise ServiceResponseException(
                f"{type(self)} service failed to complete the prompt",
                ex,
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
            ) from ex

=======
        ) from ex
        
>>>>>>> Stashed changes
<<<<<<< Updated upstream
<<<<<<< Updated upstream
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
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> head
            ) from ex

        ) from ex
        
            ) from ex

<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
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
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
        metadata: dict[str, Any] = {"id": response.id}
        # Check if usage exists and has a value, then add it to the metadata
        if hasattr(response, "usage") and response.usage is not None:
            metadata["usage"] = response.usage

<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
>>>>>>> main
        metadata: dict[str, Any] = {"id": response.id}
        # Check if usage exists and has a value, then add it to the metadata
        if hasattr(response, "usage") and response.usage is not None:
            metadata["usage"] = response.usage

<<<<<<< HEAD
>>>>>>> Stashed changes
<<<<<<< Updated upstream
        return [
            self._create_chat_message_content(response, content_block, metadata) for content_block in response.content
        ]
<<<<<<< Updated upstream
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
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> head
        return [
            self._create_chat_message_content(response, content_block, metadata) for content_block in response.content
        ]
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
        return [
            self._create_chat_message_content(response, content_block, metadata) for content_block in response.content
        ]
=======
>>>>>>> Stashed changes
        settings.messages, parsed_system_message = self._prepare_chat_history_for_request(chat_history)
        if settings.system is None and parsed_system_message is not None:
            settings.system = parsed_system_message

        return await self._send_chat_request(settings)
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
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
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head

    @override
    async def _inner_get_streaming_chat_message_contents(
        self,
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
<<<<<<< main
=======
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
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
<<<<<<< main
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
        chat_history: ChatHistory,
        settings: PromptExecutionSettings,
        **kwargs: Any,
    ) -> AsyncGenerator[list[StreamingChatMessageContent], Any]:
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
=======
>>>>>>> Stashed changes
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
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
        return [self._create_chat_message_content(response, content_block, metadata) 
                for content_block in response.content]
        
    async def get_streaming_chat_message_contents(
        self,
        chat_history: ChatHistory,
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
        settings: PromptExecutionSettings, 
        **kwargs: Any,
    ) -> AsyncGenerator[list[StreamingChatMessageContent], Any]: 
>>>>>>> Stashed changes
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< Updated upstream
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
=======
=======
<<<<<<< div
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
>>>>>>> head
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
        settings: PromptExecutionSettings,
        **kwargs: Any,
    ) -> AsyncGenerator[list[StreamingChatMessageContent], Any]: 
    ) -> AsyncGenerator[list[StreamingChatMessageContent], Any]:
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
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
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
        """Executes a streaming chat completion request and returns the result.

        Args:
            chat_history: The chat history to use for the chat completion.
            settings: The settings to use for the chat completion request.
            kwargs: The optional arguments.

<<<<<<< Updated upstream
        Yields:
            A stream of StreamingChatMessageContent.
<<<<<<< Updated upstream
        """
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< Updated upstream
=======
        """
<<<<<<< HEAD
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
        chat_history: "ChatHistory",
        settings: "PromptExecutionSettings",
    ) -> AsyncGenerator[list["StreamingChatMessageContent"], Any]:
>>>>>>> upstream/main
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
=======
>>>>>>> Stashed changes
=======
        chat_history: "ChatHistory",
        settings: "PromptExecutionSettings",
    ) -> AsyncGenerator[list["StreamingChatMessageContent"], Any]:
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
        chat_history: "ChatHistory",
        settings: "PromptExecutionSettings",
    ) -> AsyncGenerator[list["StreamingChatMessageContent"], Any]:
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
        chat_history: "ChatHistory",
        settings: "PromptExecutionSettings",
    ) -> AsyncGenerator[list["StreamingChatMessageContent"], Any]:
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> head
        if not isinstance(settings, AnthropicChatPromptExecutionSettings):
            settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(settings, AnthropicChatPromptExecutionSettings)  # nosec

<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
>>>>>>> head
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
<<<<<<< HEAD
=======
        settings.messages, parsed_system_message = self._prepare_chat_history_for_request(chat_history, stream=True)
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
        settings.messages, parsed_system_message = self._prepare_chat_history_for_request(chat_history, stream=True)
>>>>>>> main
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
        settings.messages, parsed_system_message = self._prepare_chat_history_for_request(chat_history, stream=True)
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
        settings.messages, parsed_system_message = self._prepare_chat_history_for_request(chat_history, stream=True)
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
        settings.ai_model_id = settings.ai_model_id or self.ai_model_id
        settings.messages = self._prepare_chat_history_for_request(chat_history)
        try:
            async with self.async_client.messages.stream(**settings.prepare_settings_dict()) as stream:
                author_role = None
                metadata: dict[str, Any] = {"usage": {}, "id": None}
                content_block_idx = 0
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
<<<<<<< Updated upstream

=======
                
>>>>>>> Stashed changes
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
=======
>>>>>>> Stashed changes
=======

                

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

=======
                
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======

                

<<<<<<< Updated upstream
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
<<<<<<< div
=======

                

>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> head
                async for stream_event in stream:
                    if isinstance(stream_event, RawMessageStartEvent):
                        author_role = stream_event.message.role
                        metadata["usage"]["input_tokens"] = stream_event.message.usage.input_tokens
                        metadata["id"] = stream_event.message.id
                    elif isinstance(stream_event, (RawContentBlockDeltaEvent, RawMessageDeltaEvent)):
<<<<<<< HEAD
<<<<<<< Updated upstream
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
<<<<<<< Updated upstream
=======
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
=======
>>>>>>> main
>>>>>>> Stashed changes
                        yield [
                            self._create_streaming_chat_message_content(
                                stream_event, content_block_idx, author_role, metadata
                            )
                        ]
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> main
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
                        yield [self._create_streaming_chat_message_content(stream_event, 
                                                                           content_block_idx, 
                                                                           author_role, 
                                                                           metadata)]
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
>>>>>>> main
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
<<<<<<< HEAD
=======
=======
>>>>>>> main
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
        Yields:
            A stream of StreamingChatMessageContent.
        """
<<<<<<< HEAD
=======
        chat_history: "ChatHistory",
        settings: "PromptExecutionSettings",
    ) -> AsyncGenerator[list["StreamingChatMessageContent"], Any]:
>>>>>>> upstream/main
=======
        chat_history: "ChatHistory",
        settings: "PromptExecutionSettings",
    ) -> AsyncGenerator[list["StreamingChatMessageContent"], Any]:
>>>>>>> main
        if not isinstance(settings, AnthropicChatPromptExecutionSettings):
            settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(settings, AnthropicChatPromptExecutionSettings)  # nosec

<<<<<<< HEAD
=======
        settings.messages, parsed_system_message = self._prepare_chat_history_for_request(chat_history, stream=True)
>>>>>>> main
        settings.ai_model_id = settings.ai_model_id or self.ai_model_id
        settings.messages = self._prepare_chat_history_for_request(chat_history)
        try:
            async with self.async_client.messages.stream(**settings.prepare_settings_dict()) as stream:
                author_role = None
                metadata: dict[str, Any] = {"usage": {}, "id": None}
                content_block_idx = 0
<<<<<<< HEAD
<<<<<<< Updated upstream

=======
                
>>>>>>> Stashed changes
=======

                

>>>>>>> main
                async for stream_event in stream:
                    if isinstance(stream_event, RawMessageStartEvent):
                        author_role = stream_event.message.role
                        metadata["usage"]["input_tokens"] = stream_event.message.usage.input_tokens
                        metadata["id"] = stream_event.message.id
                    elif isinstance(stream_event, (RawContentBlockDeltaEvent, RawMessageDeltaEvent)):
<<<<<<< HEAD
<<<<<<< Updated upstream
=======
>>>>>>> main
<<<<<<< div
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
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> head
                        yield [
                            self._create_streaming_chat_message_content(
                                stream_event, content_block_idx, author_role, metadata
                            )
                        ]
<<<<<<< div
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> head
<<<<<<< HEAD
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
                        yield [self._create_streaming_chat_message_content(stream_event, 
                                                                           content_block_idx, 
                                                                           author_role, 
                                                                           metadata)]
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
<<<<<<< Updated upstream
<<<<<<< div
=======
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> main
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
                        yield [self._create_streaming_chat_message_content(stream_event, 
                                                                           content_block_idx, 
                                                                           author_role, 
                                                                           metadata)]
<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> head
>>>>>>> Stashed changes
=======
>>>>>>> main
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> head
                    elif isinstance(stream_event, ContentBlockStopEvent):
                        content_block_idx += 1
        except Exception as ex:
            raise ServiceResponseException(
                f"{type(self)} service failed to complete the request",
                ex,
            ) from ex

    # endregion

    def _create_chat_message_content(
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
        self, response: Message, content: TextBlock, response_metadata: dict[str, Any]
    ) -> "ChatMessageContent":
        """Create a chat message content object."""
        items: list[ITEM_TYPES] = []

=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
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
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
=======
=======
<<<<<<< div
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
>>>>>>> head
        self, response: Message, content: TextBlock, response_metadata: dict[str, Any]
        if settings.system is None and parsed_system_message is not None:
            settings.system = parsed_system_message

        response = self._send_chat_stream_request(settings)
        if not isinstance(response, AsyncGenerator):
            raise ServiceInvalidResponseError("Expected an AsyncGenerator response.")

        async for message in response:
            yield message

    def _prepare_chat_history_for_request(
        self,
        chat_history: "ChatHistory",
        role_key: str = "role",
        content_key: str = "content",
        stream: bool = False,
    ) -> tuple[list[dict[str, Any]], str | None]:
        """Prepare the chat history for an Anthropic request.

        Allowing customization of the key names for role/author, and optionally overriding the role.

        Args:
            chat_history: The chat history to prepare.
            role_key: The key name for the role/author.
            content_key: The key name for the content/message.
            stream: Whether the request is for a streaming chat.

        Returns:
            A tuple containing the prepared chat history and the first SYSTEM message content.
        """
        system_message_content = None
        remaining_messages: list[dict[str, Any]] = []
        system_message_found = False
        for message in chat_history.messages:
            # Skip system messages after the first one is found
            if message.role == AuthorRole.SYSTEM:
                if not system_message_found:
                    system_message_content = message.content
                    system_message_found = True
            elif message.role == AuthorRole.TOOL:
                # if tool result message isn't the most recent message, add it to the remaining messages
                if not remaining_messages or remaining_messages[-1][role_key] != AuthorRole.USER:
                    remaining_messages.append({
                        role_key: AuthorRole.USER,
                        content_key: [],
                    })

                # add the tool result to the most recent message
                tool_results_message = remaining_messages[-1]
                for item in message.items:
                    if isinstance(item, FunctionResultContent):
                        tool_results_message["content"].append({
                            "type": "tool_result",
                            "tool_use_id": item.id,
                            content_key: str(item.result),
                        })
            elif message.finish_reason == SemanticKernelFinishReason.TOOL_CALLS:
                if not stream:
                    if not message.inner_content:
                        raise ServiceInvalidResponseError(
                            "Expected a message with an Anthropic Message as inner content."
                        )

                    remaining_messages.append({
                        role_key: AuthorRole.ASSISTANT,
                        content_key: [content_block.to_dict() for content_block in message.inner_content.content],
                    })
                else:
                    content: list[TextBlock | ToolUseBlock] = []
                    # for remaining items, add them to the content
                    for item in message.items:
                        if isinstance(item, TextContent):
                            content.append(TextBlock(text=item.text, type="text"))
                        elif isinstance(item, FunctionCallContent):
                            item_arguments = (
                                item.arguments if not isinstance(item.arguments, str) else json.loads(item.arguments)
                            )

                            content.append(
                                ToolUseBlock(id=item.id, input=item_arguments, name=item.name, type="tool_use")
                            )

                    remaining_messages.append({
                        role_key: AuthorRole.ASSISTANT,
                        content_key: content,
                    })
            else:
                # The API requires only role and content keys for the remaining messages
                remaining_messages.append({
                    role_key: getattr(message, role_key),
                    content_key: getattr(message, content_key),
                })

        return remaining_messages, system_message_content

    # endregion

    def _create_chat_message_content(
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        self, response: Message, response_metadata: dict[str, Any]
    ) -> "ChatMessageContent":
        """Create a chat message content object."""
        items: list[ITEM_TYPES] = []
        items += self._get_tool_calls_from_message(response)

<<<<<<< HEAD
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
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
        self, 
        response: Message, 
        content: TextBlock, 
        response_metadata: dict[str, Any]
    ) -> "ChatMessageContent":
<<<<<<< Updated upstream
        """Create a chat message content object."""
        items: list[ITEM_TYPES] = []
        
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
        if content.text:
            items.append(TextContent(text=content.text))
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
        """Create a chat message content object."""
        items: list[ITEM_TYPES] = []
        
>>>>>>> Stashed changes
<<<<<<< HEAD
>>>>>>> Stashed changes
        if content.text:
            items.append(TextContent(text=content.text))
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
        self, response: Message, content: TextBlock, response_metadata: dict[str, Any]
    ) -> "ChatMessageContent":
        """Create a chat message content object."""
        items: list[ITEM_TYPES] = []

        if content.text:
            items.append(TextContent(text=content.text))
        for content_block in response.content:
            if isinstance(content_block, TextBlock):
                items.append(TextContent(text=content_block.text))
<<<<<<< HEAD
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
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75

        finish_reason = None
        if response.stop_reason:
            finish_reason = ANTHROPIC_TO_SEMANTIC_KERNEL_FINISH_REASON_MAP[response.stop_reason]
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
<<<<<<< Updated upstream

=======
        
>>>>>>> Stashed changes
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
=======
>>>>>>> Stashed changes
=======

        

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
=======
>>>>>>> Stashed changes
        self, response: Message, response_metadata: dict[str, Any]
    ) -> "ChatMessageContent":
        """Create a chat message content object."""
        items: list[ITEM_TYPES] = []
        items += self._get_tool_calls_from_message(response)

>>>>>>> main
        self, 
        response: Message, 
        content: TextBlock, 
        response_metadata: dict[str, Any]
    ) -> "ChatMessageContent":
        """Create a chat message content object."""
        items: list[ITEM_TYPES] = []
        
<<<<<<< HEAD
>>>>>>> Stashed changes
        if content.text:
            items.append(TextContent(text=content.text))
=======
        self, response: Message, content: TextBlock, response_metadata: dict[str, Any]
    ) -> "ChatMessageContent":
        """Create a chat message content object."""
        items: list[ITEM_TYPES] = []

        if content.text:
            items.append(TextContent(text=content.text))
        for content_block in response.content:
            if isinstance(content_block, TextBlock):
                items.append(TextContent(text=content_block.text))
>>>>>>> main

        finish_reason = None
        if response.stop_reason:
            finish_reason = ANTHROPIC_TO_SEMANTIC_KERNEL_FINISH_REASON_MAP[response.stop_reason]
<<<<<<< HEAD
<<<<<<< Updated upstream

=======
        
>>>>>>> Stashed changes
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======

        

<<<<<<< Updated upstream
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
=======

        

>>>>>>> main
>>>>>>> Stashed changes
<<<<<<< div
=======

        

>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> head
        return ChatMessageContent(
            inner_content=response,
            ai_model_id=self.ai_model_id,
            metadata=response_metadata,
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
            role=AuthorRole(response.role),
=======
=======
>>>>>>> Stashed changes
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
>>>>>>> Stashed changes
            role=AuthorRole(response.role),
=======
            role=AuthorRole.ASSISTANT,
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
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
            role=AuthorRole.ASSISTANT,
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
            items=items,
            finish_reason=finish_reason,
        )

    def _create_streaming_chat_message_content(
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
        self,
        stream_event: RawContentBlockDeltaEvent | RawMessageDeltaEvent,
        content_block_idx: int,
        role: str | None = None,
<<<<<<< Updated upstream
<<<<<<< Updated upstream
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
=======
=======
>>>>>>> Stashed changes
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
        self,
        stream_event: TextEvent | ContentBlockStopEvent | RawMessageDeltaEvent,
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
        self,
        stream_event: TextEvent | ContentBlockStopEvent | RawMessageDeltaEvent,
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
        self,
        stream_event: TextEvent | ContentBlockStopEvent | RawMessageDeltaEvent,
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> head
        metadata: dict[str, Any] = {},
    ) -> StreamingChatMessageContent:
        """Create a streaming chat message content object from a choice."""
        text_content = ""

        if stream_event.delta and hasattr(stream_event.delta, "text"):
            text_content = stream_event.delta.text

        items: list[STREAMING_ITEM_TYPES] = [StreamingTextContent(choice_index=content_block_idx, text=text_content)]

<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
=======
>>>>>>> Stashed changes
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
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
        self, 
        stream_event: RawContentBlockDeltaEvent | RawMessageDeltaEvent, 
        content_block_idx: int, 
        role: str | None = None, 
        metadata: dict[str, Any] = {}
    ) -> StreamingChatMessageContent:
        """Create a streaming chat message content object from a choice."""
        text_content = ""
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
            
        if stream_event.delta and hasattr(stream_event.delta, "text"):
            text_content = stream_event.delta.text
        
        items: list[STREAMING_ITEM_TYPES] = [StreamingTextContent(choice_index=content_block_idx, text=text_content)]
        
>>>>>>> Stashed changes
        finish_reason = None
        if isinstance(stream_event, RawMessageDeltaEvent):
            if stream_event.delta.stop_reason:
                finish_reason = ANTHROPIC_TO_SEMANTIC_KERNEL_FINISH_REASON_MAP[stream_event.delta.stop_reason]

            metadata["usage"]["output_tokens"] = stream_event.usage.output_tokens

        return StreamingChatMessageContent(
            choice_index=content_block_idx,
            inner_content=stream_event,
            ai_model_id=self.ai_model_id,
            metadata=metadata,
            role=AuthorRole(role) if role else AuthorRole.ASSISTANT,
            finish_reason=finish_reason,
            items=items,
        )
<<<<<<< main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
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
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
=======
=======
<<<<<<< div
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
>>>>>>> head

        if stream_event.delta and hasattr(stream_event.delta, "text"):
            text_content = stream_event.delta.text

        items: list[STREAMING_ITEM_TYPES] = [StreamingTextContent(choice_index=content_block_idx, text=text_content)]
        

        """Create a streaming chat message content object from a content block."""
        items: list[STREAMING_ITEM_TYPES] = []
        finish_reason = None

        if isinstance(stream_event, TextEvent):
            items.append(StreamingTextContent(choice_index=0, text=stream_event.text))
        elif (
            isinstance(stream_event, ContentBlockStopEvent)
            and hasattr(stream_event, "content_block")
            and stream_event.content_block.type == "tool_use"
        ):
            tool_use_block = stream_event.content_block
            items.append(
                FunctionCallContent(
                    id=tool_use_block.id,
                    index=stream_event.index,
                    name=tool_use_block.name,
                    arguments=json.dumps(tool_use_block.input) if tool_use_block.input else None,
                )
            )
        elif isinstance(stream_event, RawMessageDeltaEvent):
            finish_reason = ANTHROPIC_TO_SEMANTIC_KERNEL_FINISH_REASON_MAP[str(stream_event.delta.stop_reason)]
            metadata["usage"]["output_tokens"] = stream_event.usage.output_tokens

        return StreamingChatMessageContent(
            choice_index=0,
            inner_content=stream_event,
            ai_model_id=self.ai_model_id,
            metadata=metadata,
            role=AuthorRole.ASSISTANT,
            finish_reason=finish_reason,
            items=items,
        )
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
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
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head

    def get_prompt_execution_settings_class(self) -> "type[AnthropicChatPromptExecutionSettings]":
        """Create a request settings object."""
        return AnthropicChatPromptExecutionSettings
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
    
>>>>>>> Stashed changes
=======
>>>>>>> upstream/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
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
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
=======
=======
<<<<<<< div
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
>>>>>>> head
    

    def update_settings_from_function_call_configuration_anthropic(
        self,
        function_choice_configuration: FunctionCallChoiceConfiguration,
        settings: "PromptExecutionSettings",
        type: "FunctionChoiceType",
    ) -> None:
        """Update the settings from a FunctionChoiceConfiguration."""
        if (
            function_choice_configuration.available_functions
            and hasattr(settings, "tools")
            and hasattr(settings, "tool_choice")
        ):
            settings.tools = [
                self.kernel_function_metadata_to_function_call_format_anthropic(f)
                for f in function_choice_configuration.available_functions
            ]

            if (
                settings.function_choice_behavior
                and settings.function_choice_behavior.type_ == FunctionChoiceType.REQUIRED
            ) or type == FunctionChoiceType.REQUIRED:
                settings.tool_choice = {"type": "any"}
            else:
                settings.tool_choice = {"type": type.value}

    def kernel_function_metadata_to_function_call_format_anthropic(
        self,
        metadata: KernelFunctionMetadata,
    ) -> dict[str, Any]:
        """Convert the kernel function metadata to function calling format."""
        return {
            "name": metadata.fully_qualified_name,
            "description": metadata.description or "",
            "input_schema": {
                "type": "object",
                "properties": {p.name: p.schema_data for p in metadata.parameters},
                "required": [p.name for p in metadata.parameters if p.is_required],
            },
        }

    @override
    def _update_function_choice_settings_callback(self):
        return self.update_settings_from_function_call_configuration_anthropic

    async def _send_chat_request(self, settings: AnthropicChatPromptExecutionSettings) -> list["ChatMessageContent"]:
        """Send the chat request."""
        try:
            response = await self.async_client.messages.create(**settings.prepare_settings_dict())
        except Exception as ex:
            raise ServiceResponseException(
                f"{type(self)} service failed to complete the request",
                ex,
            ) from ex

        response_metadata: dict[str, Any] = {"id": response.id}
        if hasattr(response, "usage") and response.usage is not None:
            response_metadata["usage"] = response.usage

        return [self._create_chat_message_content(response, response_metadata)]

    async def _send_chat_stream_request(
        self, settings: AnthropicChatPromptExecutionSettings
    ) -> AsyncGenerator[list["StreamingChatMessageContent"], None]:
        """Send the chat stream request.

        The stream yields a sequence of stream events, which are used to create streaming chat message content:
        - RawMessageStartEvent is used to determine the message id and input tokens.
        - RawMessageDeltaEvent is used to determine the finish reason.
        - TextEvent is used to determine the text content and ContentBlockStopEvent is used to determine
            the tool use content.
        """
        try:
            async with self.async_client.messages.stream(**settings.prepare_settings_dict()) as stream:
                metadata: dict[str, Any] = {"usage": {}, "id": None}
                async for stream_event in stream:
                    if isinstance(stream_event, RawMessageStartEvent):
                        metadata["usage"]["input_tokens"] = stream_event.message.usage.input_tokens
                        metadata["id"] = stream_event.message.id
                    elif isinstance(stream_event, (TextEvent, RawMessageDeltaEvent)) or (
                        isinstance(stream_event, ContentBlockStopEvent)
                        and stream_event.content_block.type == "tool_use"
                    ):
                        yield [self._create_streaming_chat_message_content(stream_event, metadata)]
        except Exception as ex:
            raise ServiceResponseException(
                f"{type(self)} service failed to complete the request",
                ex,
            ) from ex

    def _get_tool_calls_from_message(self, message: Message) -> list[FunctionCallContent]:
        """Get tool calls from a content blocks."""
        tool_calls: list[FunctionCallContent] = []

        for idx, content_block in enumerate(message.content):
            if isinstance(content_block, ToolUseBlock):
                tool_calls.append(
                    FunctionCallContent(
                        id=content_block.id,
                        index=idx,
                        name=content_block.name,
                        arguments=getattr(content_block, "input", None),
                    )
                )

        return tool_calls

    @override
    def _reset_function_choice_settings(self, settings: "PromptExecutionSettings") -> None:
        if hasattr(settings, "tool_choice"):
            settings.tool_choice = None
        if hasattr(settings, "tools"):
            settings.tools = None
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
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
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
