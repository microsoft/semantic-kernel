# Copyright (c) Microsoft. All rights reserved.

import json
from collections.abc import Callable, Mapping

from ollama._types import Message

from semantic_kernel.connectors.ai.function_call_choice_configuration import FunctionCallChoiceConfiguration
from semantic_kernel.connectors.ai.function_calling_utils import kernel_function_metadata_to_function_call_format
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceType
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.image_content import ImageContent
from semantic_kernel.contents.utils.author_role import AuthorRole


def _format_system_message(message: ChatMessageContent) -> Message:
    """Format a system message to the expected object for the client.

    Args:
        message: The system message.

    Returns:
        The formatted system message.
    """
    return Message(role="system", content=message.content)


def _format_user_message(message: ChatMessageContent) -> Message:
    """Format a user message to the expected object for the client.

    Args:
        message: The user message.

    Returns:
        The formatted user message.
    """
    if not any(isinstance(item, (ImageContent)) for item in message.items):
        return Message(role="user", content=message.content)

    user_message = Message(role="user", content=message.content)

    image_items = [item for item in message.items if isinstance(item, ImageContent)]
    if image_items:
        if any(not image_item.data for image_item in image_items):
            raise ValueError("Image item must contain data encoded as base64.")
        user_message["images"] = [image_item.data for image_item in image_items]

    return user_message


def _format_assistant_message(message: ChatMessageContent) -> Message:
    """Format an assistant message to the expected object for the client.

    Args:
        message: The assistant message.

    Returns:
        The formatted assistant message.
    """
    assistant_message = Message(role="assistant", content=message.content)

    image_items = [item for item in message.items if isinstance(item, ImageContent)]
    if image_items:
        if any(image_item.data is None for image_item in image_items):
            raise ValueError("Image must be encoded as base64.")
        assistant_message["images"] = [image_item.data for image_item in image_items]

    tool_calls = [item for item in message.items if isinstance(item, FunctionCallContent)]
    if tool_calls:
        assistant_message["tool_calls"] = [
            {
                "function": {
                    "name": tool_call.function_name,
                    "arguments": tool_call.arguments
                    if isinstance(tool_call.arguments, Mapping)
                    else json.loads(tool_call.arguments or "{}"),
                }
            }
            for tool_call in tool_calls
        ]

    return assistant_message


def _format_tool_message(message: ChatMessageContent) -> Message:
    """Format a tool message to the expected object for the client.

    Args:
        message: The tool message.

    Returns:
        The formatted tool message.
    """
    function_result_items = [item for item in message.items if isinstance(item, FunctionResultContent)]
    if not function_result_items:
        raise ValueError("Tool message must have a function result content item.")

    return Message(role="tool", content=str(function_result_items[0].result))


MESSAGE_CONVERTERS: dict[AuthorRole, Callable[[ChatMessageContent], Message]] = {
    AuthorRole.SYSTEM: _format_system_message,
    AuthorRole.USER: _format_user_message,
    AuthorRole.ASSISTANT: _format_assistant_message,
    AuthorRole.TOOL: _format_tool_message,
}


def update_settings_from_function_choice_configuration(
    function_choice_configuration: FunctionCallChoiceConfiguration,
    settings: PromptExecutionSettings,
    type: FunctionChoiceType,
) -> None:
    """Update the settings from a FunctionChoiceConfiguration.

    Since this function might be called before the settings are cast to Ollama Settings
    We need to try to use the tools attribute or fallback to the extension_data attribute.
    """
    if function_choice_configuration.available_functions:
        tools = [
            kernel_function_metadata_to_function_call_format(f)
            for f in function_choice_configuration.available_functions
        ]
        try:
            settings.tools = tools  # type: ignore
        except Exception:
            settings.extension_data["tools"] = tools
