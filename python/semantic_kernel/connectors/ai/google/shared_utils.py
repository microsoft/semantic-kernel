# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
from collections.abc import Callable
from typing import TYPE_CHECKING

from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior, FunctionChoiceType
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.exceptions.service_exceptions import (
    ServiceInvalidExecutionSettingsError,
    ServiceInvalidRequestError,
)
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata
from semantic_kernel.kernel import Kernel

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.google.google_ai.google_ai_prompt_execution_settings import (
        GoogleAIChatPromptExecutionSettings,
    )
    from semantic_kernel.connectors.ai.google.vertex_ai.vertex_ai_prompt_execution_settings import (
        VertexAIChatPromptExecutionSettings,
    )

logger: logging.Logger = logging.getLogger(__name__)


def filter_system_message(chat_history: ChatHistory) -> str | None:
    """Filter the first system message from the chat history.

    If there are multiple system messages, raise an error.
    If there are no system messages, return None.
    """
    if len([message for message in chat_history if message.role == AuthorRole.SYSTEM]) > 1:
        raise ServiceInvalidRequestError(
            "Multiple system messages in chat history. Only one system message is expected."
        )

    for message in chat_history:
        if message.role == AuthorRole.SYSTEM:
            return message.content

    return None


async def invoke_function_calls(
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


FUNCTION_CHOICE_TYPE_TO_GOOGLE_FUNCTION_CALLING_MODE = {
    FunctionChoiceType.AUTO: "AUTO",
    FunctionChoiceType.NONE: "NONE",
    FunctionChoiceType.REQUIRED: "ANY",
}

# The separator used in the fully qualified name of the function instead of the default "-" separator.
# This is required since Gemini doesn't work well with "-" in the function name.
# https://ai.google.dev/gemini-api/docs/function-calling#function_declarations
GEMINI_FUNCTION_NAME_SEPARATOR = "_"


def format_function_result_content_name_to_gemini_function_name(function_result_content: FunctionResultContent) -> str:
    """Format the function result content name to the Gemini function name."""
    return (
        f"{function_result_content.plugin_name}{GEMINI_FUNCTION_NAME_SEPARATOR}{function_result_content.function_name}"
        if function_result_content.plugin_name
        else function_result_content.function_name
    )


def format_kernel_function_fully_qualified_name_to_gemini_function_name(metadata: KernelFunctionMetadata) -> str:
    """Format the kernel function fully qualified name to the Gemini function name."""
    return (
        f"{metadata.plugin_name}{GEMINI_FUNCTION_NAME_SEPARATOR}{metadata.name}"
        if metadata.plugin_name
        else metadata.name
    )


def format_gemini_function_name_to_kernel_function_fully_qualified_name(gemini_function_name: str) -> str:
    """Format the Gemini function name to the kernel function fully qualified name."""
    if GEMINI_FUNCTION_NAME_SEPARATOR in gemini_function_name:
        plugin_name, function_name = gemini_function_name.split(GEMINI_FUNCTION_NAME_SEPARATOR, 1)
        return f"{plugin_name}-{function_name}"
    return gemini_function_name


def configure_function_choice_behavior(
    settings: "GoogleAIChatPromptExecutionSettings | VertexAIChatPromptExecutionSettings",
    kernel: Kernel,
    callback: Callable[..., None],
):
    """Configure the function choice behavior to include the kernel functions."""
    if not settings.function_choice_behavior:
        raise ServiceInvalidExecutionSettingsError("Function choice behavior is required for tool calls.")

    settings.function_choice_behavior.configure(kernel=kernel, update_settings_callback=callback, settings=settings)
