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
GEMINI_FUNCTION_NAME_SEPARATOR = "_"


def format_gemini_function_name_to_kernel_function_fully_qualified_name(gemini_function_name: str) -> str:
    """Format the Gemini function name to the kernel function fully qualified name."""
    if GEMINI_FUNCTION_NAME_SEPARATOR in gemini_function_name:
        plugin_name, function_name = gemini_function_name.split(GEMINI_FUNCTION_NAME_SEPARATOR, 1)
        return f"{plugin_name}{DEFAULT_FULLY_QUALIFIED_NAME_SEPARATOR}{function_name}"
    return gemini_function_name
