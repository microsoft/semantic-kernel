# Copyright (c) Microsoft. All rights reserved.

import asyncio
import json
from collections.abc import Callable, Mapping
from functools import partial
from typing import Any

from semantic_kernel.connectors.ai.bedrock.bedrock_prompt_execution_settings import BedrockChatPromptExecutionSettings
from semantic_kernel.connectors.ai.function_call_choice_configuration import FunctionCallChoiceConfiguration
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceType
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.const import DEFAULT_FULLY_QUALIFIED_NAME_SEPARATOR
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.image_content import ImageContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.contents.utils.finish_reason import FinishReason
from semantic_kernel.exceptions.service_exceptions import ServiceInvalidRequestError


async def run_in_executor(executor, func, *args, **kwargs):
    """Run a function in an executor."""
    return await asyncio.get_event_loop().run_in_executor(executor, partial(func, *args, **kwargs))


def remove_none_recursively(data: dict, max_depth: int = 5) -> dict:
    """Remove None values from a dictionary recursively."""
    if max_depth <= 0:
        return data

    if not isinstance(data, dict):
        return data

    return {k: remove_none_recursively(v, max_depth=max_depth - 1) for k, v in data.items() if v is not None}


def _format_system_message(message: ChatMessageContent) -> dict[str, str]:
    """Format a system message to the expected object for the client.

    Note that Guardrails are currently not supported.

    Args:
        message: The system message.

    Returns:
        The formatted system message.
    """
    return {"text": message.content}


def _format_user_message(message: ChatMessageContent) -> dict[str, Any]:
    """Format a user message to the expected object for the client.

    Note that Guardrails and Documents are currently not supported.

    Args:
        message: The user message.

    Returns:
        The formatted user message.
    """
    contents: list[Any] = []
    for item in message.items:
        if not isinstance(item, (ImageContent, TextContent)):
            raise ServiceInvalidRequestError("Only text and image content are supported in a user message.")

        if isinstance(item, ImageContent):
            contents.append({
                "image": {
                    "format": item.mime_type.removeprefix("image/"),
                    "source": {
                        "bytes": item.data,
                    },
                }
            })
        else:
            contents.append({"text": item.text})

    return {
        "role": "user",
        "content": contents,
    }


def _format_assistant_message(message: ChatMessageContent) -> dict[str, Any]:
    """Format an assistant message to the expected object for the client.

    Note that Guardrails and documents are currently not supported.

    Args:
        message: The assistant message.

    Returns:
        The formatted assistant message.
    """
    contents: list[Any] = []
    for item in message.items:
        if isinstance(item, ImageContent):
            raise ServiceInvalidRequestError("Image content is not supported in an assistant message.")

        if isinstance(item, TextContent):
            contents.append({"text": item.text})
        elif isinstance(item, FunctionCallContent):
            contents.append({
                "toolUse": {
                    "toolUseId": item.id,
                    "name": item.custom_fully_qualified_name(BEDROCK_FUNCTION_NAME_SEPARATOR),
                    "input": item.arguments
                    if isinstance(item.arguments, Mapping)
                    else json.loads(item.arguments or "{}"),
                }
            })
        else:
            raise ServiceInvalidRequestError(f"Unsupported content type in an assistant message: {type(item)}")

    return {
        "role": "assistant",
        "content": contents,
    }


def _format_tool_message(message: ChatMessageContent) -> dict[str, Any]:
    """Format a tool message to the expected object for the client.

    Args:
        message: The tool message.

    Returns:
        The formatted tool message.
    """
    contents: list[Any] = []
    for item in message.items:
        if isinstance(item, ImageContent):
            raise ServiceInvalidRequestError("Image content is not supported in a tool message.")

        if isinstance(item, TextContent):
            contents.append({"text": item.text})
        elif isinstance(item, FunctionResultContent):
            contents.append({
                "toolResult": {
                    "toolUseId": item.id,
                    # Image and document content are not yet supported in a tool message by SK
                    "content": [{"text": str(item)}],
                }
            })
        else:
            raise ServiceInvalidRequestError(f"Unsupported content type in a tool message: {type(item)}")

    return {
        "role": "user",
        "content": contents,
    }


MESSAGE_CONVERTERS: dict[AuthorRole, Callable[[ChatMessageContent], dict[str, Any]]] = {
    AuthorRole.SYSTEM: _format_system_message,
    AuthorRole.USER: _format_user_message,
    AuthorRole.ASSISTANT: _format_assistant_message,
    AuthorRole.TOOL: _format_tool_message,
}

# The separator used in the fully qualified name of the function instead of the default "-" separator.
# This is required since Bedrock disallows "-" in the function name.
# https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_ToolSpecification.html#API_runtime_ToolSpecification_Contents
BEDROCK_FUNCTION_NAME_SEPARATOR = "_"


def format_bedrock_function_name_to_kernel_function_fully_qualified_name(bedrock_function_name: str) -> str:
    """Format the Bedrock function name to the kernel function fully qualified name."""
    if BEDROCK_FUNCTION_NAME_SEPARATOR in bedrock_function_name:
        plugin_name, function_name = bedrock_function_name.split(BEDROCK_FUNCTION_NAME_SEPARATOR, 1)
        return f"{plugin_name}{DEFAULT_FULLY_QUALIFIED_NAME_SEPARATOR}{function_name}"
    return bedrock_function_name


def update_settings_from_function_choice_configuration(
    function_choice_configuration: FunctionCallChoiceConfiguration,
    settings: PromptExecutionSettings,
    type: FunctionChoiceType,
) -> None:
    """Update the settings from a FunctionChoiceConfiguration."""
    assert isinstance(settings, BedrockChatPromptExecutionSettings)  # nosec

    # Bedrock supports 3 types of tool choice behavior: auto, any, tool
    # We will map our `FunctionChoiceType` to the corresponding Bedrock type following these rules:
    # `FunctionChoiceType.NONE` -> No configuration needed
    # `FunctionChoiceType.AUTO` -> "auto"
    # `FunctionChoiceType.REQUIRED`:
    #   - If there are more than one available functions -> "any"
    #   - If there is only one available function -> "tool"
    if type == FunctionChoiceType.NONE:
        return

    if function_choice_configuration.available_functions:
        if type == FunctionChoiceType.AUTO:
            settings.tool_choice = {"auto": {}}
        elif type == FunctionChoiceType.REQUIRED:
            if len(function_choice_configuration.available_functions) > 1:
                settings.tool_choice = {"any": {}}
            else:
                settings.tool_choice = {
                    "tool": {
                        "name": function_choice_configuration.available_functions[0].custom_fully_qualified_name(
                            BEDROCK_FUNCTION_NAME_SEPARATOR
                        ),
                    }
                }

        settings.tools = [
            {
                "toolSpec": {
                    "name": function.custom_fully_qualified_name(BEDROCK_FUNCTION_NAME_SEPARATOR),
                    "description": function.description or "",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {param.name: param.schema_data for param in function.parameters},
                            "required": [p.name for p in function.parameters if p.is_required],
                        }
                    },
                }
            }
            for function in function_choice_configuration.available_functions
        ]


def finish_reason_from_bedrock_to_semantic_kernel(finish_reason: str) -> FinishReason | None:
    """Convert a finish reason from Bedrock to Semantic Kernel."""
    return {
        "stop_sequence": FinishReason.STOP,
        "end_turn": FinishReason.STOP,
        "max_tokens": FinishReason.LENGTH,
        "content_filtered": FinishReason.CONTENT_FILTER,
        "tool_use": FinishReason.TOOL_CALLS,
    }.get(finish_reason)
