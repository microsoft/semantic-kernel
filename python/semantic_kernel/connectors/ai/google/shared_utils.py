# Copyright (c) Microsoft. All rights reserved.

import logging

from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceType
from semantic_kernel.const import DEFAULT_FULLY_QUALIFIED_NAME_SEPARATOR
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.exceptions.service_exceptions import ServiceInvalidRequestError

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


FUNCTION_CHOICE_TYPE_TO_GOOGLE_FUNCTION_CALLING_MODE = {
    FunctionChoiceType.AUTO: "AUTO",
    FunctionChoiceType.NONE: "NONE",
    FunctionChoiceType.REQUIRED: "ANY",
}

# The separator used in the fully qualified name of the function instead of the default "-" separator.
# This is required since Gemini doesn't work well with "-" in the function name.
# https://ai.google.dev/gemini-api/docs/function-calling#function_declarations
# Using double underscore to avoid situations where the function name already contains a single underscore.
# For example, we may incorrect split a function name with a single score when the function doesn't have a plugin name.
GEMINI_FUNCTION_NAME_SEPARATOR = "__"


def format_gemini_function_name_to_kernel_function_fully_qualified_name(gemini_function_name: str) -> str:
    """Format the Gemini function name to the kernel function fully qualified name."""
    if GEMINI_FUNCTION_NAME_SEPARATOR in gemini_function_name:
        plugin_name, function_name = gemini_function_name.split(GEMINI_FUNCTION_NAME_SEPARATOR, 1)
        return f"{plugin_name}{DEFAULT_FULLY_QUALIFIED_NAME_SEPARATOR}{function_name}"
    return gemini_function_name


def collapse_function_call_results_in_chat_history(chat_history: ChatHistory):
    """The Gemini API expects the results of parallel function calls to be contained in a single message to be returned.

    This helper method collapses the results of parallel function calls in the chat history into a single Tool message.

    Since this method in an internal method that is supposed to be called only by the Google AI and Vertex AI
    connectors, it is safe to assume that the chat history contains a correct sequence of messages, i.e. there won't be
    cases where the assistant wants to call 2 functions in parallel but there are more than 2 function results following
    the assistant message.
    """
    if not chat_history.messages:
        return

    current_idx = 1
    while current_idx < len(chat_history):
        previous_message = chat_history[current_idx - 1]
        current_message = chat_history[current_idx]
        if previous_message.role == AuthorRole.TOOL and current_message.role == AuthorRole.TOOL:
            previous_message.items.extend(current_message.items)
            chat_history.remove_message(current_message)
        else:
            current_idx += 1
