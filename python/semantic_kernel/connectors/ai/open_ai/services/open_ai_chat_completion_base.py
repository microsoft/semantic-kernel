# Copyright (c) Microsoft. All rights reserved.

import sys
from collections.abc import AsyncGenerator, Callable
from typing import TYPE_CHECKING, Any, ClassVar, cast

from semantic_kernel.connectors.ai.function_call_choice_configuration import FunctionCallChoiceConfiguration
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.utils.telemetry.model_diagnostics.decorators import trace_chat_completion

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
=======
>>>>>>> Stashed changes
>>>>>>> head

from openai import AsyncStream
from openai.types.chat.chat_completion import ChatCompletion, Choice
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk, ChoiceDeltaFunctionCall, ChoiceDeltaToolCall
from openai.types.chat.chat_completion_chunk import Choice as ChunkChoice
from openai.types.chat.chat_completion_message import FunctionCall
from openai.types.chat.chat_completion_message_tool_call import ChatCompletionMessageToolCall
from typing_extensions import deprecated

<<<<<<< div
=======
=======
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
>>>>>>> head

from openai import AsyncStream
from openai.types.chat.chat_completion import ChatCompletion, Choice
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk, ChoiceDeltaFunctionCall, ChoiceDeltaToolCall
from openai.types.chat.chat_completion_chunk import Choice as ChunkChoice
from openai.types.chat.chat_completion_message import FunctionCall
from openai.types.chat.chat_completion_message_tool_call import ChatCompletionMessageToolCall
from typing_extensions import deprecated

<<<<<<< div
>>>>>>> main
=======
<<<<<<< Updated upstream
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
from semantic_kernel.connectors.ai.chat_completion_client_base import (
    ChatCompletionClientBase,
)
from semantic_kernel.connectors.ai.function_call_behavior import FunctionCallBehavior
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
from semantic_kernel.connectors.ai.function_calling_utils import (
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
<<<<<<< Updated upstream
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
<<<<<<< main
from semantic_kernel.connectors.ai.function_calling_utils import (
<<<<<<< main
=======
from semantic_kernel.connectors.ai.function_calling_utils import (
>>>>>>> origin/main
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
from semantic_kernel.connectors.ai.function_calling_utils import (
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
from semantic_kernel.connectors.ai.function_calling_utils import (
>>>>>>> main
=======
>>>>>>> head
    update_settings_from_function_call_configuration,
)
from semantic_kernel.connectors.ai.function_choice_behavior import (
    FunctionChoiceBehavior,
)
<<<<<<< div
<<<<<<< div
=======
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
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
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
=======
from semantic_kernel.connectors.ai.function_calling_utils import (
>>>>>>> origin/main
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
from semantic_kernel.connectors.ai.function_calling_utils import (
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
from semantic_kernel.connectors.ai.function_calling_utils import (
>>>>>>> main
=======
>>>>>>> head
    merge_function_results,
    update_settings_from_function_call_configuration,
)
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
<<<<<<< main
>>>>>>> Stashed changes
>>>>>>> upstream/main
=======
from semantic_kernel.connectors.ai.function_calling_utils import update_settings_from_function_call_configuration
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior, FunctionChoiceType
>>>>>>> upstream/main
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
>>>>>>> Stashed changes
=======
from semantic_kernel.connectors.ai.function_calling_utils import update_settings_from_function_call_configuration
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior, FunctionChoiceType
>>>>>>> origin/main
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
<<<<<<< div
from semantic_kernel.connectors.ai.function_calling_utils import update_settings_from_function_call_configuration
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior, FunctionChoiceType
>>>>>>> main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
from semantic_kernel.connectors.ai.function_calling_utils import update_settings_from_function_call_configuration
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior, FunctionChoiceType
>>>>>>> origin/main
>>>>>>> head
from semantic_kernel.connectors.ai.function_calling_utils import (
    update_settings_from_function_call_configuration,
)
from semantic_kernel.connectors.ai.function_choice_behavior import (
    FunctionChoiceBehavior,
)
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> origin/PR
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
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
>>>>>>> origin/PR
=======
from semantic_kernel.connectors.ai.open_ai.contents import OpenAIChatMessageContent, OpenAIStreamingChatMessageContent
from semantic_kernel.connectors.ai.open_ai.models.chat_completion.function_call import FunctionCall
from semantic_kernel.connectors.ai.open_ai.models.chat_completion.tool_calls import ToolCall
>>>>>>> origin/main
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
from semantic_kernel.connectors.ai.open_ai.contents import OpenAIChatMessageContent, OpenAIStreamingChatMessageContent
from semantic_kernel.connectors.ai.open_ai.models.chat_completion.function_call import FunctionCall
from semantic_kernel.connectors.ai.open_ai.models.chat_completion.tool_calls import ToolCall
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
from semantic_kernel.connectors.ai.open_ai.contents import OpenAIChatMessageContent, OpenAIStreamingChatMessageContent
from semantic_kernel.connectors.ai.open_ai.models.chat_completion.function_call import FunctionCall
from semantic_kernel.connectors.ai.open_ai.models.chat_completion.tool_calls import ToolCall
>>>>>>> main
=======
>>>>>>> head
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_prompt_execution_settings import (
    OpenAIChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_handler import OpenAIHandler
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.streaming_chat_message_content import (
    StreamingChatMessageContent,
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
)
from semantic_kernel.contents.streaming_text_content import StreamingTextContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.contents.utils.finish_reason import FinishReason
from semantic_kernel.exceptions import (
    ServiceInvalidExecutionSettingsError,
    ServiceInvalidResponseError,
)
from semantic_kernel.filters.auto_function_invocation.auto_function_invocation_context import (
    AutoFunctionInvocationContext,
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
>>>>>>> Stashed changes
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
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
=======
>>>>>>> origin/main
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
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
from semantic_kernel.utils.telemetry.decorators import trace_chat_completion
from semantic_kernel.exceptions import (
    ServiceInvalidExecutionSettingsError,
    ServiceInvalidResponseError,
)
from semantic_kernel.filters.auto_function_invocation.auto_function_invocation_context import (
    AutoFunctionInvocationContext,
)
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
>>>>>>> origin/PR
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
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
>>>>>>> origin/PR
=======
from semantic_kernel.utils.telemetry.model_diagnostics import trace_chat_completion
from semantic_kernel.contents.chat_role import ChatRole
from semantic_kernel.contents.finish_reason import FinishReason
>>>>>>> origin/main
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
)
from semantic_kernel.contents.streaming_text_content import StreamingTextContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.contents.utils.finish_reason import FinishReason
from semantic_kernel.exceptions import (
    ServiceInvalidExecutionSettingsError,
    ServiceInvalidResponseError,
)
from semantic_kernel.filters.auto_function_invocation.auto_function_invocation_context import (
    AutoFunctionInvocationContext,
)
from semantic_kernel.utils.telemetry.decorators import trace_chat_completion
from semantic_kernel.exceptions import (
    ServiceInvalidExecutionSettingsError,
    ServiceInvalidResponseError,
)
from semantic_kernel.filters.auto_function_invocation.auto_function_invocation_context import (
    AutoFunctionInvocationContext,
)
from semantic_kernel.utils.telemetry.model_diagnostics import trace_chat_completion
from semantic_kernel.contents.chat_role import ChatRole
from semantic_kernel.contents.finish_reason import FinishReason
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
)
from semantic_kernel.contents.streaming_text_content import StreamingTextContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.contents.utils.finish_reason import FinishReason
from semantic_kernel.exceptions import (
    ServiceInvalidExecutionSettingsError,
    ServiceInvalidResponseError,
)
from semantic_kernel.filters.auto_function_invocation.auto_function_invocation_context import (
    AutoFunctionInvocationContext,
)
from semantic_kernel.utils.telemetry.decorators import trace_chat_completion
from semantic_kernel.exceptions import (
    ServiceInvalidExecutionSettingsError,
    ServiceInvalidResponseError,
)
from semantic_kernel.filters.auto_function_invocation.auto_function_invocation_context import (
    AutoFunctionInvocationContext,
)
from semantic_kernel.utils.telemetry.model_diagnostics import trace_chat_completion
from semantic_kernel.contents.chat_role import ChatRole
from semantic_kernel.contents.finish_reason import FinishReason
>>>>>>> main
=======
>>>>>>> head

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.prompt_execution_settings import (
        PromptExecutionSettings,
    )
    from semantic_kernel.functions.kernel_arguments import KernelArguments
    from semantic_kernel.kernel import Kernel

<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< main
logger: logging.Logger = logging.getLogger(__name__)
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
logger: logging.Logger = logging.getLogger(__name__)
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
logger: logging.Logger = logging.getLogger(__name__)
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
logger: logging.Logger = logging.getLogger(__name__)
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
logger: logging.Logger = logging.getLogger(__name__)
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
logger: logging.Logger = logging.getLogger(__name__)
=======
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
=======
>>>>>>> Stashed changes
<<<<<<< main
<<<<<<< main
logger: logging.Logger = logging.getLogger(__name__)
=======
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
logger: logging.Logger = logging.getLogger(__name__)


class InvokeTermination(Exception):
    """Exception for termination of function invocation."""
<<<<<<< div
<<<<<<< div
=======
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
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
>>>>>>> origin/main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
<<<<<<< div
=======
>>>>>>> main
=======
>>>>>>> head


class InvokeTermination(Exception):
    """Exception for termination of function invocation."""
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
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes

=======
>>>>>>> upstream/main

class OpenAIChatCompletionBase(OpenAIHandler, ChatCompletionClientBase):
    """OpenAI Chat completion class."""
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head

    MODEL_PROVIDER_NAME: ClassVar[str] = "openai"
    SUPPORTS_FUNCTION_CALLING: ClassVar[bool] = True

    # region Overriding base class methods
    # most of the methods are overridden from the ChatCompletionClientBase class, otherwise it is mentioned
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes

    # Override from AIServiceClientBase
    @override
    def get_prompt_execution_settings_class(self) -> type["PromptExecutionSettings"]:
        return OpenAIChatPromptExecutionSettings

    @override
    @trace_chat_completion(MODEL_PROVIDER_NAME)
    async def _inner_get_chat_message_contents(
        self,
        chat_history: "ChatHistory",
        settings: "PromptExecutionSettings",
    ) -> list["ChatMessageContent"]:
        if not isinstance(settings, OpenAIChatPromptExecutionSettings):
            settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(settings, OpenAIChatPromptExecutionSettings)  # nosec

<<<<<<< main
        # For backwards compatibility we need to convert the `FunctionCallBehavior` to `FunctionChoiceBehavior`
        # if this method is called with a `FunctionCallBehavior` object as part of the settings
        if hasattr(settings, "function_call_behavior") and isinstance(
            settings.function_call_behavior, FunctionCallBehavior
        ):
            settings.function_choice_behavior = (
                FunctionChoiceBehavior.from_function_call_behavior(
                    settings.function_call_behavior
                )
            )
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
>>>>>>> Stashed changes
=======

=======

    MODEL_PROVIDER_NAME: ClassVar[str] = "openai"
    SUPPORTS_FUNCTION_CALLING: ClassVar[bool] = True

    # region Overriding base class methods
    # most of the methods are overridden from the ChatCompletionClientBase class, otherwise it is mentioned

<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
=======

>>>>>>> Stashed changes
=======
=======

>>>>>>> Stashed changes
>>>>>>> head
    # Override from AIServiceClientBase
    @override
    def get_prompt_execution_settings_class(self) -> type["PromptExecutionSettings"]:
        return OpenAIChatPromptExecutionSettings
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
=======
>>>>>>> Stashed changes
>>>>>>> head

    @override
    @trace_chat_completion(MODEL_PROVIDER_NAME)
    async def _inner_get_chat_message_contents(
        self,
        chat_history: "ChatHistory",
        settings: "PromptExecutionSettings",
    ) -> list["ChatMessageContent"]:
        if not isinstance(settings, OpenAIChatPromptExecutionSettings):
            settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(settings, OpenAIChatPromptExecutionSettings)  # nosec

<<<<<<< div
=======
=======
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
>>>>>>> head

    @override
    @trace_chat_completion(MODEL_PROVIDER_NAME)
    async def _inner_get_chat_message_contents(
        self,
        chat_history: "ChatHistory",
        settings: "PromptExecutionSettings",
    ) -> list["ChatMessageContent"]:
        if not isinstance(settings, OpenAIChatPromptExecutionSettings):
            settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(settings, OpenAIChatPromptExecutionSettings)  # nosec

<<<<<<< div
>>>>>>> main
=======
<<<<<<< Updated upstream
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
        # For backwards compatibility we need to convert the `FunctionCallBehavior` to `FunctionChoiceBehavior`
        # if this method is called with a `FunctionCallBehavior` object as part of the settings
        if hasattr(settings, "function_call_behavior") and isinstance(
            settings.function_call_behavior, FunctionCallBehavior
        ):
            settings.function_choice_behavior = (
                FunctionChoiceBehavior.from_function_call_behavior(
                    settings.function_call_behavior
                )
            )
    def get_chat_message_content_class(self) -> type[ChatMessageContent]:
        """Get the chat message content types used by a class, default is ChatMessageContent."""
        return OpenAIChatMessageContent

    async def complete_chat(
        self,
        chat_history: ChatHistory,
        settings: OpenAIPromptExecutionSettings,
    ) -> List[OpenAIChatMessageContent]:
        """Executes a chat completion request and returns the result.

        Arguments:
            chat_history {ChatHistory} -- The chat history to use for the chat completion.
            settings {OpenAIChatPromptExecutionSettings | AzureChatPromptExecutionSettings} -- The settings to use
                for the chat completion request.
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
>>>>>>> origin/main
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
<<<<<<< div
>>>>>>> main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
>>>>>>> head

        kernel = kwargs.get("kernel", None)
        if settings.function_choice_behavior is not None:
            if kernel is None:
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< main
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
=======
>>>>>>> Stashed changes
<<<<<<< main
<<<<<<< main
=======
>>>>>>> origin/main
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
                raise ServiceInvalidExecutionSettingsError(
                    "The kernel is required for OpenAI tool calls."
                )
            if (
                settings.number_of_responses is not None
                and settings.number_of_responses > 1
            ):
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
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
<<<<<<< main
=======
=======
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
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
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
<<<<<<< div
=======
>>>>>>> main
=======
>>>>>>> head
                raise ServiceInvalidExecutionSettingsError("The kernel is required for OpenAI tool calls.")
        Returns:
            List[ChatMessageContent]: The completion result(s).
        """
        # For backwards compatibility we need to convert the `FunctionCallBehavior` to `FunctionChoiceBehavior`
        # if this method is called with a `FunctionCallBehavior` object as pat of the settings
        if hasattr(settings, "function_call_behavior") and isinstance(
            settings.function_call_behavior, FunctionCallBehavior
        ):
            settings.function_choice_behavior = FunctionChoiceBehavior.from_function_call_behavior(
                settings.function_call_behavior
            )
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head

        kernel = kwargs.get("kernel", None)
        arguments = kwargs.get("arguments", None)
        if settings.function_choice_behavior is not None:
            if kernel is None:
                raise ServiceInvalidExecutionSettingsError("The kernel is required for OpenAI tool calls.")
            if arguments is None and settings.function_choice_behavior.auto_invoke_kernel_functions:
                raise ServiceInvalidExecutionSettingsError(
                    "The kernel arguments are required for auto invoking OpenAI tool calls."
                )
            if settings.number_of_responses is not None and settings.number_of_responses > 1:
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
>>>>>>> origin/PR
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
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
>>>>>>> origin/PR
=======
>>>>>>> origin/main
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
>>>>>>> Stashed changes
                raise ServiceInvalidExecutionSettingsError(
                    "Auto-invocation of tool calls may only be used with a "
                    "OpenAIChatPromptExecutions.number_of_responses of 1."
                )

<<<<<<< Updated upstream
=======

        kernel = kwargs.get("kernel", None)
        arguments = kwargs.get("arguments", None)
        if settings.function_choice_behavior is not None:
            if kernel is None:
                raise ServiceInvalidExecutionSettingsError("The kernel is required for OpenAI tool calls.")
            if arguments is None and settings.function_choice_behavior.auto_invoke_kernel_functions:
                raise ServiceInvalidExecutionSettingsError(
                    "The kernel arguments are required for auto invoking OpenAI tool calls."
                )
            if settings.number_of_responses is not None and settings.number_of_responses > 1:
=======
>>>>>>> Stashed changes
                raise ServiceInvalidExecutionSettingsError(
                    "Auto-invocation of tool calls may only be used with a "
                    "OpenAIChatPromptExecutions.number_of_responses of 1."
                )

<<<<<<< div
=======

        kernel = kwargs.get("kernel", None)
        arguments = kwargs.get("arguments", None)
        if settings.function_choice_behavior is not None:
            if kernel is None:
                raise ServiceInvalidExecutionSettingsError("The kernel is required for OpenAI tool calls.")
            if arguments is None and settings.function_choice_behavior.auto_invoke_kernel_functions:
                raise ServiceInvalidExecutionSettingsError(
                    "The kernel arguments are required for auto invoking OpenAI tool calls."
                )
            if settings.number_of_responses is not None and settings.number_of_responses > 1:
                raise ServiceInvalidExecutionSettingsError(
                    "Auto-invocation of tool calls may only be used with a "
                    "OpenAIChatPromptExecutions.number_of_responses of 1."
                )

>>>>>>> main
=======
<<<<<<< Updated upstream
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
        # behavior for non-function calling or for enable, but not auto-invoke.
        self._prepare_settings(
            settings, chat_history, stream_request=False, kernel=kernel
        )
        if settings.function_choice_behavior is None or (
            settings.function_choice_behavior
            and not settings.function_choice_behavior.auto_invoke_kernel_functions
        ):
            return await self._send_chat_request(settings)

        # loop for auto-invoke function calls
        for request_index in range(
            settings.function_choice_behavior.maximum_auto_invoke_attempts
        ):
            completions = await self._send_chat_request(settings)
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< main
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
=======
>>>>>>> Stashed changes
<<<<<<< main
<<<<<<< main
=======
>>>>>>> origin/main
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
            # there is only one chat message, this was checked earlier
            chat_history.add_message(message=completions[0])
            # get the function call contents from the chat message
            function_calls = [
                item
                for item in chat_history.messages[-1].items
                if isinstance(item, FunctionCallContent)
            ]
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
            # get the function call contents from the chat message, there is only one chat message
            # this was checked earlier
            function_calls = [item for item in completions[0].items if isinstance(item, FunctionCallContent)]
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
            # get the function call contents from the chat message, there is only one chat message
            # this was checked earlier
            function_calls = [item for item in completions[0].items if isinstance(item, FunctionCallContent)]
            # get the function call contents from the chat message, there is only one chat message
            # this was checked earlier
            function_calls = [item for item in completions[0].items if isinstance(item, FunctionCallContent)]
>>>>>>> origin/main
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
<<<<<<< div
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> head
            # get the function call contents from the chat message, there is only one chat message
            # this was checked earlier
            function_calls = [item for item in completions[0].items if isinstance(item, FunctionCallContent)]
            # get the function call contents from the chat message, there is only one chat message
            # this was checked earlier
            function_calls = [item for item in completions[0].items if isinstance(item, FunctionCallContent)]
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
>>>>>>> head
            if (fc_count := len(function_calls)) == 0:
                return completions

            # Since we have a function call, add the assistant's tool call message to the history
            chat_history.add_message(message=completions[0])
<<<<<<< div
<<<<<<< div
=======
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< main
>>>>>>> Stashed changes
<<<<<<< Updated upstream
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes

            logger.info(f"processing {fc_count} tool calls in parallel.")

            # this function either updates the chat history with the function call results
            # or returns the context, with terminate set to True
            # in which case the loop will break and the function calls are returned.
            results = await asyncio.gather(
                *[
                    self._process_function_call(
                        function_call=function_call,
                        chat_history=chat_history,
                        kernel=kernel,
                        arguments=kwargs.get("arguments", None),
                        function_call_count=fc_count,
                        request_index=request_index,
                        function_call_behavior=settings.function_choice_behavior,
                    )
                    for function_call in function_calls
                ],
            )

            if any(result.terminate for result in results if result is not None):
                return merge_function_results(chat_history.messages[-len(results) :])
=======
        settings.stream = False
        settings.messages = self._prepare_chat_history_for_request(chat_history)
        settings.ai_model_id = settings.ai_model_id or self.ai_model_id
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
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> head

            logger.info(f"processing {fc_count} tool calls in parallel.")

            # this function either updates the chat history with the function call results
            # or returns the context, with terminate set to True
            # in which case the loop will break and the function calls are returned.
            results = await asyncio.gather(
                *[
                    self._process_function_call(
                        function_call=function_call,
                        chat_history=chat_history,
                        kernel=kernel,
                        arguments=kwargs.get("arguments", None),
                        function_call_count=fc_count,
                        request_index=request_index,
                        function_call_behavior=settings.function_choice_behavior,
                    )
                    for function_call in function_calls
                ],
            )

            if any(result.terminate for result in results if result is not None):
                return merge_function_results(chat_history.messages[-len(results) :])
        settings.messages = self._prepare_chat_history_for_request(chat_history)
        settings.stream = False
        settings.messages = self._prepare_chat_history_for_request(chat_history)
        settings.ai_model_id = settings.ai_model_id or self.ai_model_id

<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
>>>>>>> origin/main
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
<<<<<<< div
>>>>>>> main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
>>>>>>> head
        response = await self._send_request(request_settings=settings)
        assert isinstance(response, ChatCompletion)  # nosec
        response_metadata = self._get_metadata_from_chat_response(response)
        return [self._create_chat_message_content(response, choice, response_metadata) for choice in response.choices]

    @override
    async def _inner_get_streaming_chat_message_contents(
        self,
        chat_history: "ChatHistory",
        settings: "PromptExecutionSettings",
    ) -> AsyncGenerator[list["StreamingChatMessageContent"], Any]:
        if not isinstance(settings, OpenAIChatPromptExecutionSettings):
            settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(settings, OpenAIChatPromptExecutionSettings)  # nosec
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< main
>>>>>>> Stashed changes
<<<<<<< Updated upstream
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes

<<<<<<< main
<<<<<<< main
=======
    ) -> AsyncGenerator[list[StreamingChatMessageContent | None], Any]:
        """Executes a streaming chat completion request and returns the result.

        Args:
            chat_history (ChatHistory): The chat history to use for the chat completion.
            settings (OpenAIChatPromptExecutionSettings | AzureChatPromptExecutionSettings): The settings to use
                for the chat completion request.
            kwargs (Dict[str, Any]): The optional arguments.

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
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> head

    ) -> AsyncGenerator[list[StreamingChatMessageContent | None], Any]:
        """Executes a streaming chat completion request and returns the result.

        Args:
            chat_history (ChatHistory): The chat history to use for the chat completion.
            settings (OpenAIChatPromptExecutionSettings | AzureChatPromptExecutionSettings): The settings to use
        chat_history: ChatHistory,
        settings: OpenAIPromptExecutionSettings,
    ) -> AsyncIterable[List[OpenAIStreamingChatMessageContent]]:
        """Executes a streaming chat completion request and returns the result.

        Arguments:
            chat_history {ChatHistory} -- The chat history to use for the chat completion.
            settings {OpenAIChatPromptExecutionSettings | AzureChatPromptExecutionSettings} -- The settings to use
                for the chat completion request.
            kwargs (Dict[str, Any]): The optional arguments.

<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
>>>>>>> origin/main
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
<<<<<<< div
>>>>>>> main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
>>>>>>> head
        Yields:
            List[StreamingChatMessageContent]: A stream of
                StreamingChatMessageContent when using Azure.
        """
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> origin/PR
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
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
>>>>>>> origin/PR
=======
>>>>>>> origin/main
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
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
        # For backwards compatibility we need to convert the `FunctionCallBehavior` to `FunctionChoiceBehavior`
        # if this method is called with a `FunctionCallBehavior` object as part of the settings
        if hasattr(settings, "function_call_behavior") and isinstance(
            settings.function_call_behavior, FunctionCallBehavior
        ):
            settings.function_choice_behavior = (
                FunctionChoiceBehavior.from_function_call_behavior(
                    settings.function_call_behavior
                )
            )

        kernel = kwargs.get("kernel", None)
        if settings.function_choice_behavior is not None:
            if kernel is None:
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< main
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
<<<<<<< main
<<<<<<< main
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
<<<<<<< main
<<<<<<< main
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
>>>>>>> head
                raise ServiceInvalidExecutionSettingsError(
                    "The kernel is required for OpenAI tool calls."
                )
            if (
                settings.number_of_responses is not None
                and settings.number_of_responses > 1
            ):
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
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
>>>>>>> Stashed changes
<<<<<<< main
=======
=======
>>>>>>> origin/main
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
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
>>>>>>> main
=======
>>>>>>> head
                raise ServiceInvalidExecutionSettingsError("The kernel is required for OpenAI tool calls.")
        arguments = kwargs.get("arguments", None)
        if settings.function_choice_behavior is not None:
            if kernel is None:
                raise ServiceInvalidExecutionSettingsError("The kernel is required for OpenAI tool calls.")
            if arguments is None and settings.function_choice_behavior.auto_invoke_kernel_functions:
                raise ServiceInvalidExecutionSettingsError(
                    "The kernel arguments are required for auto invoking OpenAI tool calls."
                )
            if settings.number_of_responses is not None and settings.number_of_responses > 1:
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> origin/PR
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
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
>>>>>>> origin/PR
=======
>>>>>>> origin/main
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
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
>>>>>>> main
=======
>>>>>>> head
                raise ServiceInvalidExecutionSettingsError(
                    "Auto-invocation of tool calls may only be used with a "
                    "OpenAIChatPromptExecutions.number_of_responses of 1."
                )

        # Prepare settings for streaming requests
        self._prepare_settings(
            settings, chat_history, stream_request=True, kernel=kernel
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< main
>>>>>>> Stashed changes
<<<<<<< Updated upstream
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
>>>>>>> head
        )

        request_attempts = (
            settings.function_choice_behavior.maximum_auto_invoke_attempts
            if (
                settings.function_choice_behavior
                and settings.function_choice_behavior.auto_invoke_kernel_functions
            )
            else 1
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
>>>>>>> head
        )
        # hold the messages, if there are more than one response, it will not be used, so we flatten
        for request_index in range(request_attempts):
            all_messages: list[StreamingChatMessageContent] = []
            function_call_returned = False
            async for messages in self._send_chat_stream_request(settings):
                for msg in messages:
                    if msg is not None:
                        all_messages.append(msg)
                        if any(
                            isinstance(item, FunctionCallContent) for item in msg.items
                        ):
                            function_call_returned = True
                yield messages

            if (
                settings.function_choice_behavior is None
                or (
                    settings.function_choice_behavior
                    and not settings.function_choice_behavior.auto_invoke_kernel_functions
                )
                or not function_call_returned
            ):
                # no need to process function calls
                # note that we don't check the FinishReason and instead check whether there are any tool calls,
                # as the service may return a FinishReason of "stop" even if there are tool calls to be made,
                # in particular if a required tool is specified.
                return

            # there is one response stream in the messages, combining now to create the full completion
            # depending on the prompt, the message may contain both function call content and others
            full_completion: StreamingChatMessageContent = reduce(
                lambda x, y: x + y, all_messages
            )
            function_calls = [
                item
                for item in full_completion.items
                if isinstance(item, FunctionCallContent)
            ]
            chat_history.add_message(message=full_completion)

            fc_count = len(function_calls)
            logger.info(f"processing {fc_count} tool calls in parallel.")

            # this function either updates the chat history with the function call results
            # or returns the context, with terminate set to True
            # in which case the loop will break and the function calls are returned.
            # Exceptions are not caught, that is up to the developer, can be done with a filter
            results = await asyncio.gather(
                *[
                    self._process_function_call(
                        function_call=function_call,
                        chat_history=chat_history,
                        kernel=kernel,
                        arguments=kwargs.get("arguments", None),
                        function_call_count=fc_count,
                        request_index=request_index,
                        function_call_behavior=settings.function_choice_behavior,
                    )
                    for function_call in function_calls
                ],
            )
            if any(result.terminate for result in results if result is not None):
                yield merge_function_results(chat_history.messages[-len(results) :])  # type: ignore
                break

<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
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
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
        request_attempts = (
            settings.function_choice_behavior.maximum_auto_invoke_attempts
            if (
                settings.function_choice_behavior
                and settings.function_choice_behavior.auto_invoke_kernel_functions
            )
            else 1
        )
        # hold the messages, if there are more than one response, it will not be used, so we flatten
        for request_index in range(request_attempts):
            all_messages: list[StreamingChatMessageContent] = []
            function_call_returned = False
            async for messages in self._send_chat_stream_request(settings):
                for msg in messages:
                    if msg is not None:
                        all_messages.append(msg)
                        if any(
                            isinstance(item, FunctionCallContent) for item in msg.items
                        ):
                            function_call_returned = True
                yield messages

            if (
                settings.function_choice_behavior is None
                or (
                    settings.function_choice_behavior
                    and not settings.function_choice_behavior.auto_invoke_kernel_functions
                )
                or not function_call_returned
            ):
                # no need to process function calls
                # note that we don't check the FinishReason and instead check whether there are any tool calls,
                # as the service may return a FinishReason of "stop" even if there are tool calls to be made,
                # in particular if a required tool is specified.
                return

            # there is one response stream in the messages, combining now to create the full completion
            # depending on the prompt, the message may contain both function call content and others
            full_completion: StreamingChatMessageContent = reduce(
                lambda x, y: x + y, all_messages
            )
            function_calls = [
                item
                for item in full_completion.items
                if isinstance(item, FunctionCallContent)
            ]
            chat_history.add_message(message=full_completion)

            fc_count = len(function_calls)
            logger.info(f"processing {fc_count} tool calls in parallel.")

            # this function either updates the chat history with the function call results
            # or returns the context, with terminate set to True
            # in which case the loop will break and the function calls are returned.
            # Exceptions are not caught, that is up to the developer, can be done with a filter
            results = await asyncio.gather(
                *[
                    self._process_function_call(
                        function_call=function_call,
                        chat_history=chat_history,
                        kernel=kernel,
                        arguments=kwargs.get("arguments", None),
                        function_call_count=fc_count,
                        request_index=request_index,
                        function_call_behavior=settings.function_choice_behavior,
                    )
                    for function_call in function_calls
                ],
            )
            if any(result.terminate for result in results if result is not None):
                yield merge_function_results(chat_history.messages[-len(results) :])  # type: ignore
                break

>>>>>>> origin/main
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
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
>>>>>>> main
=======
>>>>>>> head
            self._update_settings(settings, chat_history, kernel=kernel)

    # endregion
    # region internal handlers

    async def _send_chat_request(
        self, settings: OpenAIChatPromptExecutionSettings
    ) -> list["ChatMessageContent"]:
        """Send the chat request."""
        response = await self._send_request(request_settings=settings)
        assert isinstance(response, ChatCompletion)  # nosec
        response_metadata = self._get_metadata_from_chat_response(response)
        return [
            self._create_chat_message_content(response, choice, response_metadata)
            for choice in response.choices
        ]
<<<<<<< div
<<<<<<< div
=======
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
        settings.stream = True
        settings.messages = self._prepare_chat_history_for_request(chat_history)
        settings.ai_model_id = settings.ai_model_id or self.ai_model_id
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
>>>>>>> origin/main
=======
=======
>>>>>>> Stashed changes
=======
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> Stashed changes
>>>>>>> head
        settings.messages = self._prepare_chat_history_for_request(chat_history)
        settings.stream = True
        settings.stream_options = {"include_usage": True}
        settings.messages = self._prepare_chat_history_for_request(chat_history)
        settings.ai_model_id = settings.ai_model_id or self.ai_model_id
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
>>>>>>> origin/main
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
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
>>>>>>> head

        response = await self._send_request(request_settings=settings)
        if not isinstance(response, AsyncStream):
            raise ServiceInvalidResponseError(
                "Expected an AsyncStream[ChatCompletionChunk] response."
            )
        async for chunk in response:
<<<<<<< div
<<<<<<< div
=======
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
            if len(chunk.choices) == 0:
                continue
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
            if len(chunk.choices) == 0 and chunk.usage is None:
                continue
<<<<<<< main
=======

>>>>>>> origin/main
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
            if len(chunk.choices) == 0 and chunk.usage is None:
                continue
<<<<<<< div

>>>>>>> main
=======
=======
=======
>>>>>>> Stashed changes
>>>>>>> origin/main

        response = await self._send_request(request_settings=settings)
        if not isinstance(response, AsyncStream):
            raise ServiceInvalidResponseError(
                "Expected an AsyncStream[ChatCompletionChunk] response."
<<<<<<< Updated upstream
            )
        async for chunk in response:
            if len(chunk.choices) == 0 and chunk.usage is None:
                continue
<<<<<<< main
=======
>>>>>>> Stashed changes

>>>>>>> origin/main
>>>>>>> head
            assert isinstance(chunk, ChatCompletionChunk)  # nosec
            chunk_metadata = self._get_metadata_from_streaming_chat_response(chunk)
            yield [
                self._create_streaming_chat_message_content(
                    chunk, choice, chunk_metadata
                )
                for choice in chunk.choices
            ]
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< head
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
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
>>>>>>> head
            if chunk.usage is not None:
                # Usage is contained in the last chunk where the choices are empty
                # We are duplicating the usage metadata to all the choices in the response
                yield [
                    StreamingChatMessageContent(
                        role=AuthorRole.ASSISTANT,
                        content="",
                        choice_index=i,
                        inner_content=chunk,
                        ai_model_id=settings.ai_model_id,
                        metadata=chunk_metadata,
                    )
                    for i in range(settings.number_of_responses or 1)
                ]
            else:
                yield [
                    self._create_streaming_chat_message_content(chunk, choice, chunk_metadata)
                    for choice in chunk.choices
                ]
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> origin/main
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
=======
>>>>>>> Stashed changes
>>>>>>> origin/main

    @override
    def _verify_function_choice_settings(self, settings: "PromptExecutionSettings") -> None:
        if not isinstance(settings, OpenAIChatPromptExecutionSettings):
            raise ServiceInvalidExecutionSettingsError("The settings must be an OpenAIChatPromptExecutionSettings.")
        if settings.number_of_responses is not None and settings.number_of_responses > 1:
            raise ServiceInvalidExecutionSettingsError(
                "Auto-invocation of tool calls may only be used with a "
                "OpenAIChatPromptExecutions.number_of_responses of 1."
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
<<<<<<< Updated upstream
<<<<<<< head
=======
>>>>>>> Stashed changes

    # endregion

    # region content creation

    def _create_chat_message_content(
        self,
        response: ChatCompletion,
        choice: Choice,
        response_metadata: dict[str, Any],
    ) -> "ChatMessageContent":
        """Create a chat message content object from a choice."""
        metadata = self._get_metadata_from_chat_choice(choice)
        metadata.update(response_metadata)

        items: list[Any] = self._get_tool_calls_from_chat_choice(choice)
        items.extend(self._get_function_call_from_chat_choice(choice))
        if choice.message.content:
            items.append(TextContent(text=choice.message.content))
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
<<<<<<< main
=======
        elif hasattr(choice.message, "refusal") and choice.message.refusal:
            items.append(TextContent(text=choice.message.refusal))
>>>>>>> head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
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

        return ChatMessageContent(
            inner_content=response,
            ai_model_id=self.ai_model_id,
            metadata=metadata,
            role=AuthorRole(choice.message.role),
            items=items,
            finish_reason=(
                FinishReason(choice.finish_reason) if choice.finish_reason else None
            ),
        )

    def _create_streaming_chat_message_content(
        self,
        chunk: ChatCompletionChunk,
        choice: ChunkChoice,
        chunk_metadata: dict[str, Any],
    ) -> StreamingChatMessageContent:
        """Create a streaming chat message content object from a choice."""
        metadata = self._get_metadata_from_chat_choice(choice)
        metadata.update(chunk_metadata)

        items: list[Any] = self._get_tool_calls_from_chat_choice(choice)
        items.extend(self._get_function_call_from_chat_choice(choice))
<<<<<<< main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< main
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
=======
            )
        async for chunk in response:
            if len(chunk.choices) == 0 and chunk.usage is None:
                continue
<<<<<<< main
=======

>>>>>>> origin/main
            assert isinstance(chunk, ChatCompletionChunk)  # nosec
            chunk_metadata = self._get_metadata_from_streaming_chat_response(chunk)
            yield [
                self._create_streaming_chat_message_content(
                    chunk, choice, chunk_metadata
                )
                for choice in chunk.choices
            ]
<<<<<<< main
=======
            if chunk.usage is not None:
                # Usage is contained in the last chunk where the choices are empty
                # We are duplicating the usage metadata to all the choices in the response
                yield [
                    StreamingChatMessageContent(
                        role=AuthorRole.ASSISTANT,
                        content="",
                        choice_index=i,
                        inner_content=chunk,
                        ai_model_id=settings.ai_model_id,
                        metadata=chunk_metadata,
                    )
                    for i in range(settings.number_of_responses or 1)
                ]
            else:
                yield [
                    self._create_streaming_chat_message_content(chunk, choice, chunk_metadata)
                    for choice in chunk.choices
                ]
>>>>>>> origin/main
>>>>>>> head

    @override
    def _verify_function_choice_settings(self, settings: "PromptExecutionSettings") -> None:
        if not isinstance(settings, OpenAIChatPromptExecutionSettings):
            raise ServiceInvalidExecutionSettingsError("The settings must be an OpenAIChatPromptExecutionSettings.")
        if settings.number_of_responses is not None and settings.number_of_responses > 1:
            raise ServiceInvalidExecutionSettingsError(
                "Auto-invocation of tool calls may only be used with a "
                "OpenAIChatPromptExecutions.number_of_responses of 1."
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
<<<<<<< div
<<<<<<< div
=======
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
>>>>>>> head

    # endregion

    # region content creation

    def _create_chat_message_content(
        self,
        response: ChatCompletion,
        choice: Choice,
        response_metadata: dict[str, Any],
    ) -> "ChatMessageContent":
        """Create a chat message content object from a choice."""
        metadata = self._get_metadata_from_chat_choice(choice)
        metadata.update(response_metadata)

        items: list[Any] = self._get_tool_calls_from_chat_choice(choice)
        items.extend(self._get_function_call_from_chat_choice(choice))
        if choice.message.content:
            items.append(TextContent(text=choice.message.content))
<<<<<<< Updated upstream
<<<<<<< div
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
        elif hasattr(choice.message, "refusal") and choice.message.refusal:
            items.append(TextContent(text=choice.message.refusal))
>>>>>>> head
=======
<<<<<<< main
=======
        elif hasattr(choice.message, "refusal") and choice.message.refusal:
            items.append(TextContent(text=choice.message.refusal))
>>>>>>> origin/main
>>>>>>> Stashed changes

        return ChatMessageContent(
            inner_content=response,
            ai_model_id=self.ai_model_id,
            metadata=metadata,
            role=AuthorRole(choice.message.role),
            items=items,
            finish_reason=(
                FinishReason(choice.finish_reason) if choice.finish_reason else None
            ),
        )

    def _create_streaming_chat_message_content(
        self,
        chunk: ChatCompletionChunk,
        choice: ChunkChoice,
        chunk_metadata: dict[str, Any],
    ) -> StreamingChatMessageContent:
        """Create a streaming chat message content object from a choice."""
        metadata = self._get_metadata_from_chat_choice(choice)
        metadata.update(chunk_metadata)

        items: list[Any] = self._get_tool_calls_from_chat_choice(choice)
        items.extend(self._get_function_call_from_chat_choice(choice))
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< main
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
=======
<<<<<<< main
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
<<<<<<< main
<<<<<<< main
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
<<<<<<< div
=======

    # endregion

    # region content creation

    def _create_chat_message_content(
        self,
        response: ChatCompletion,
        choice: Choice,
        response_metadata: dict[str, Any],
    ) -> "ChatMessageContent":
        """Create a chat message content object from a choice."""
        metadata = self._get_metadata_from_chat_choice(choice)
        metadata.update(response_metadata)

        items: list[Any] = self._get_tool_calls_from_chat_choice(choice)
        items.extend(self._get_function_call_from_chat_choice(choice))
        if choice.message.content:
            items.append(TextContent(text=choice.message.content))
        elif hasattr(choice.message, "refusal") and choice.message.refusal:
            items.append(TextContent(text=choice.message.refusal))

        return ChatMessageContent(
            inner_content=response,
            ai_model_id=self.ai_model_id,
            metadata=metadata,
            role=AuthorRole(choice.message.role),
            items=items,
            finish_reason=(
                FinishReason(choice.finish_reason) if choice.finish_reason else None
            ),
        )

    def _create_streaming_chat_message_content(
        self,
        chunk: ChatCompletionChunk,
        choice: ChunkChoice,
        chunk_metadata: dict[str, Any],
    ) -> StreamingChatMessageContent:
        """Create a streaming chat message content object from a choice."""
        metadata = self._get_metadata_from_chat_choice(choice)
        metadata.update(chunk_metadata)

        items: list[Any] = self._get_tool_calls_from_chat_choice(choice)
        items.extend(self._get_function_call_from_chat_choice(choice))
>>>>>>> main
=======
>>>>>>> head
        if choice.delta.content is not None:
            items.append(
                StreamingTextContent(
                    choice_index=choice.index, text=choice.delta.content
                )
            )
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< main
>>>>>>> Stashed changes
<<<<<<< Updated upstream
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
        if choice.delta and choice.delta.content is not None:
            items.append(StreamingTextContent(choice_index=choice.index, text=choice.delta.content))
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
=======
        if choice.delta and choice.delta.content is not None:
            items.append(StreamingTextContent(choice_index=choice.index, text=choice.delta.content))
>>>>>>> origin/main
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
<<<<<<< div
        if choice.delta and choice.delta.content is not None:
            items.append(StreamingTextContent(choice_index=choice.index, text=choice.delta.content))
>>>>>>> main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
        if choice.delta and choice.delta.content is not None:
            items.append(StreamingTextContent(choice_index=choice.index, text=choice.delta.content))
>>>>>>> origin/main
>>>>>>> head
        return StreamingChatMessageContent(
            choice_index=choice.index,
            inner_content=chunk,
            ai_model_id=self.ai_model_id,
            metadata=metadata,
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< main
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
=======
>>>>>>> Stashed changes
<<<<<<< main
<<<<<<< main
=======
>>>>>>> origin/main
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
            role=(
                AuthorRole(choice.delta.role)
                if choice.delta.role
                else AuthorRole.ASSISTANT
            ),
            finish_reason=(
                FinishReason(choice.finish_reason) if choice.finish_reason else None
            ),
<<<<<<< div
<<<<<<< div
=======
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
            role=(AuthorRole(choice.delta.role) if choice.delta and choice.delta.role else AuthorRole.ASSISTANT),
            finish_reason=(FinishReason(choice.finish_reason) if choice.finish_reason else None),
>>>>>>> upstream/main
            items=items,
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
>>>>>>> origin/main
=======
=======
>>>>>>> Stashed changes
=======
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> Stashed changes
>>>>>>> head
            role=(AuthorRole(choice.delta.role) if choice.delta and choice.delta.role else AuthorRole.ASSISTANT),
            finish_reason=(FinishReason(choice.finish_reason) if choice.finish_reason else None),
            items=items,
            role=ChatRole(choice.delta.role) if choice.delta.role else None,
            content=choice.delta.content,
            finish_reason=FinishReason(choice.finish_reason) if choice.finish_reason else None,
            function_call=self._get_function_call_from_chat_choice(choice),
            tool_calls=self._get_tool_calls_from_chat_choice(choice),
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
>>>>>>> origin/main
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
<<<<<<< div
>>>>>>> main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
>>>>>>> head
        )

    def _get_metadata_from_chat_response(
        self, response: ChatCompletion
    ) -> dict[str, Any]:
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
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
<<<<<<< main
=======
    def _get_metadata_from_chat_response(self, response: ChatCompletion) -> dict[str, Any]:
>>>>>>> origin/main
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
    def _get_metadata_from_chat_response(self, response: ChatCompletion) -> dict[str, Any]:
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
    def _get_metadata_from_chat_response(self, response: ChatCompletion) -> dict[str, Any]:
>>>>>>> main
=======
>>>>>>> head
        """Get metadata from a chat response."""
        return {
            "id": response.id,
            "created": response.created,
            "system_fingerprint": response.system_fingerprint,
            "usage": response.usage if hasattr(response, "usage") else None,
        }

    def _get_metadata_from_streaming_chat_response(
        self, response: ChatCompletionChunk
    ) -> dict[str, Any]:
        """Get metadata from a streaming chat response."""
        return {
            "id": response.id,
            "created": response.created,
            "system_fingerprint": response.system_fingerprint,
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
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
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
            "usage": CompletionUsage.from_openai(response.usage) if response.usage is not None else None,
>>>>>>> origin/main
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
            "usage": CompletionUsage.from_openai(response.usage) if response.usage is not None else None,
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
            "usage": CompletionUsage.from_openai(response.usage) if response.usage is not None else None,
>>>>>>> main
=======
>>>>>>> head
        }

    def _get_metadata_from_chat_choice(
        self, choice: Choice | ChunkChoice
    ) -> dict[str, Any]:
        """Get metadata from a chat choice."""
        return {
            "logprobs": getattr(choice, "logprobs", None),
        }

    def _get_tool_calls_from_chat_choice(
        self, choice: Choice | ChunkChoice
    ) -> list[FunctionCallContent]:
        """Get tool calls from a chat choice."""
        content = choice.message if isinstance(choice, Choice) else choice.delta
        if content and (tool_calls := getattr(content, "tool_calls", None)) is not None:
            return [
                FunctionCallContent(
                    id=tool.id,
                    index=getattr(tool, "index", None),
                    name=tool.function.name,
                    arguments=tool.function.arguments,
                )
                for tool in cast(list[ChatCompletionMessageToolCall] | list[ChoiceDeltaToolCall], tool_calls)
                if tool.function is not None
            ]
        # When you enable asynchronous content filtering in Azure OpenAI, you may receive empty deltas
        return []

    def _get_function_call_from_chat_choice(
        self, choice: Choice | ChunkChoice
    ) -> list[FunctionCallContent]:
        """Get a function call from a chat choice."""
        content = choice.message if isinstance(choice, Choice) else choice.delta
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< main
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
=======
>>>>>>> Stashed changes
<<<<<<< main
<<<<<<< main
=======
>>>>>>> origin/main
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
        assert hasattr(content, "function_call")  # nosec
        if content.function_call is None:
            return []
        return [
            FunctionCallContent(
                id="legacy_function_call",
                name=content.function_call.name,
                arguments=content.function_call.arguments,
            )
        ]
<<<<<<< div
<<<<<<< div
=======
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
=======
>>>>>>> Stashed changes
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
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
=======
>>>>>>> origin/main
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
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
        if content and (function_call := getattr(content, "function_call", None)) is not None:
            function_call = cast(FunctionCall | ChoiceDeltaFunctionCall, function_call)
            return [
                FunctionCallContent(
                    id="legacy_function_call", name=function_call.name, arguments=function_call.arguments
                )
            ]
        # When you enable asynchronous content filtering in Azure OpenAI, you may receive empty deltas
        return []
<<<<<<< div
<<<<<<< div
=======
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< main
>>>>>>> Stashed changes
<<<<<<< Updated upstream
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
>>>>>>> upstream/main

    # endregion

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

    # endregion

>>>>>>> origin/main
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
<<<<<<< div

    # endregion

>>>>>>> main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======

    # endregion

>>>>>>> origin/main
>>>>>>> head
    def _prepare_settings(
        self,
        settings: OpenAIChatPromptExecutionSettings,
        chat_history: ChatHistory,
        stream_request: bool = False,
        kernel: "Kernel | None" = None,
    ) -> None:
        """Prepare the prompt execution settings for the chat request."""
        settings.stream = stream_request
        if not settings.ai_model_id:
            settings.ai_model_id = self.ai_model_id
        self._update_settings(
            settings=settings, chat_history=chat_history, kernel=kernel
        )

    def _update_settings(
        self,
        settings: OpenAIChatPromptExecutionSettings,
        chat_history: ChatHistory,
        kernel: "Kernel | None" = None,
    ) -> None:
        """Update the settings with the chat history."""
        settings.messages = self._prepare_chat_history_for_request(chat_history)
        if settings.function_choice_behavior and kernel:
            settings.function_choice_behavior.configure(
                kernel=kernel,
                update_settings_callback=update_settings_from_function_call_configuration,
                settings=settings,
            )

    # endregion
    # region function calling

    @deprecated(
        "Use `invoke_function_call` from the kernel instead with `FunctionChoiceBehavior`."
    )
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< main
>>>>>>> Stashed changes
<<<<<<< Updated upstream
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
    # region function calling
    @deprecated("Use `invoke_function_call` from the kernel instead with `FunctionChoiceBehavior`.")
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
    # region function calling
    @deprecated("Use `invoke_function_call` from the kernel instead with `FunctionChoiceBehavior`.")
>>>>>>> origin/main
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
<<<<<<< div
    # region function calling
    @deprecated("Use `invoke_function_call` from the kernel instead with `FunctionChoiceBehavior`.")
>>>>>>> main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
    # region function calling
    @deprecated("Use `invoke_function_call` from the kernel instead with `FunctionChoiceBehavior`.")
>>>>>>> origin/main
>>>>>>> head
    async def _process_function_call(
        self,
        function_call: FunctionCallContent,
        chat_history: ChatHistory,
        kernel: "Kernel",
        arguments: "KernelArguments | None",
        function_call_count: int,
        request_index: int,
        function_call_behavior: FunctionChoiceBehavior | FunctionCallBehavior,
    ) -> "AutoFunctionInvocationContext | None":
        """Processes the tool calls in the result and update the chat history."""
        # deprecated and might not even be used anymore, hard to trigger directly
        if isinstance(function_call_behavior, FunctionCallBehavior):  # pragma: no cover
        if isinstance(function_call_behavior, FunctionCallBehavior):
            # We need to still support a `FunctionCallBehavior` input so it doesn't break current
            # customers. Map from `FunctionCallBehavior` -> `FunctionChoiceBehavior`
            function_call_behavior = FunctionChoiceBehavior.from_function_call_behavior(
                function_call_behavior
            )

        return await kernel.invoke_function_call(
            function_call=function_call,
            chat_history=chat_history,
            arguments=arguments,
            function_call_count=function_call_count,
            request_index=request_index,
            function_behavior=function_call_behavior,
        )

    # endregion
