# Copyright (c) Microsoft. All rights reserved.

from collections import OrderedDict
from collections.abc import Callable
from copy import deepcopy
from typing import TYPE_CHECKING, Any

from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError
from semantic_kernel.utils.feature_stage_decorator import experimental

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.function_choice_behavior import (
        FunctionCallChoiceConfiguration,
        FunctionChoiceType,
    )
    from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
    from semantic_kernel.contents.chat_message_content import ChatMessageContent
    from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
    from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata
    from semantic_kernel.kernel import Kernel


def update_settings_from_function_call_configuration(
    function_choice_configuration: "FunctionCallChoiceConfiguration",
    settings: "PromptExecutionSettings",
    type: "FunctionChoiceType",
) -> None:
    """Update the settings from a FunctionChoiceConfiguration."""
    if (
        function_choice_configuration.available_functions
        and hasattr(settings, "tool_choice")
        and hasattr(settings, "tools")
    ):
        settings.tool_choice = type
        settings.tools = [
            kernel_function_metadata_to_function_call_format(f)
            for f in function_choice_configuration.available_functions
        ]


def kernel_function_metadata_to_function_call_format(
    metadata: "KernelFunctionMetadata",
) -> dict[str, Any]:
    """Convert the kernel function metadata to function calling format."""
    return {
        "type": "function",
        "function": {
            "name": metadata.fully_qualified_name,
            "description": metadata.description or "",
            "parameters": {
                "type": "object",
                "properties": {
                    param.name: param.schema_data for param in metadata.parameters if param.include_in_function_choices
                },
                "required": [p.name for p in metadata.parameters if p.is_required and p.include_in_function_choices],
            },
        },
    }


def kernel_function_metadata_to_response_function_call_format(
    metadata: "KernelFunctionMetadata",
) -> dict[str, Any]:
    """Convert the kernel function metadata to function calling format."""
    return {
        "type": "function",
        "name": metadata.fully_qualified_name,
        "description": metadata.description or "",
        "parameters": {
            "type": "object",
            "properties": {
                param.name: param.schema_data for param in metadata.parameters if param.include_in_function_choices
            },
            "required": [p.name for p in metadata.parameters if p.is_required and p.include_in_function_choices],
        },
    }


def _combine_filter_dicts(*dicts: dict[str, list[str]]) -> dict:
    """Combine multiple filter dictionaries with list values into one dictionary.

    This method is ensuring unique values while preserving order.
    """
    combined_filters = {}

    keys = set().union(*(d.keys() for d in dicts))

    for key in keys:
        combined_functions: OrderedDict[str, None] = OrderedDict()
        for d in dicts:
            if key in d:
                if isinstance(d[key], list):
                    for item in d[key]:
                        combined_functions[item] = None
                else:
                    raise ServiceInitializationError(f"Values for filter key '{key}' are not lists.")
        combined_filters[key] = list(combined_functions.keys())

    return combined_filters


def merge_function_results(
    messages: list["ChatMessageContent"],
) -> list["ChatMessageContent"]:
    """Combine multiple function result content types to one chat message content type.

    This method combines the FunctionResultContent items from separate ChatMessageContent messages,
    and is used in the event that the `context.terminate = True` condition is met.
    """
    from semantic_kernel.contents.chat_message_content import ChatMessageContent
    from semantic_kernel.contents.function_result_content import FunctionResultContent

    items: list[Any] = []
    for message in messages:
        items.extend([item for item in message.items if isinstance(item, FunctionResultContent)])
    return [
        ChatMessageContent(
            role=AuthorRole.TOOL,
            items=items,
        )
    ]


def merge_streaming_function_results(
    messages: list["ChatMessageContent | StreamingChatMessageContent"],
    ai_model_id: str | None = None,
    function_invoke_attempt: int | None = None,
) -> list["StreamingChatMessageContent"]:
    """Combine multiple streaming function result content types to one streaming chat message content type.

    This method combines the FunctionResultContent items from separate StreamingChatMessageContent messages,
    and is used in the event that the `context.terminate = True` condition is met.

    Args:
        messages: The list of streaming chat message content types.
        ai_model_id: The AI model ID.
        function_invoke_attempt: The function invoke attempt.

    Returns:
        The combined streaming chat message content type.
    """
    from semantic_kernel.contents.function_result_content import FunctionResultContent
    from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent

    items: list[Any] = []
    for message in messages:
        items.extend([item for item in message.items if isinstance(item, FunctionResultContent)])

    return [
        StreamingChatMessageContent(
            role=AuthorRole.TOOL,
            items=items,
            choice_index=0,
            ai_model_id=ai_model_id,
            function_invoke_attempt=function_invoke_attempt,
        )
    ]


@experimental
def prepare_settings_for_function_calling(
    settings: "PromptExecutionSettings",
    settings_class: type["PromptExecutionSettings"],
    update_settings_callback: Callable[..., None],
    kernel: "Kernel",
) -> "PromptExecutionSettings":
    """Prepare settings for the service.

    Args:
        settings: Prompt execution settings.
        settings_class: The settings class.
        update_settings_callback: The callback to update the settings.
        kernel: Kernel instance.

    Returns:
        PromptExecutionSettings of type settings_class.
    """
    settings = deepcopy(settings)
    if not isinstance(settings, settings_class):
        settings = settings_class.from_prompt_execution_settings(settings)

    if settings.function_choice_behavior:
        # Configure the function choice behavior into the settings object
        # that will become part of the request to the AI service
        settings.function_choice_behavior.configure(
            kernel=kernel,
            update_settings_callback=update_settings_callback,
            settings=settings,
        )
    return settings
