# Copyright (c) Microsoft. All rights reserved.

from collections import OrderedDict
from typing import TYPE_CHECKING, Any

from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.function_choice_behavior import (
        FunctionCallChoiceConfiguration,
    )
    from semantic_kernel.connectors.ai.prompt_execution_settings import (
        PromptExecutionSettings,
    )
    from semantic_kernel.functions.kernel_function_metadata import (
        KernelFunctionMetadata,
    )
>>>>>>>+main
ionChoic        FunctionChoiceType,
    )
    from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
    from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata
>>>>>>>+upstream/main
nfiguration(
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
import logging
from typing import TYPE_CHECKING, Any

from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_prompt_execution_settings import (
    OpenAIChatPromptExecutionSettings,
)
from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.function_choice_behavior import (
        FunctionCallChoiceConfiguration,
    )
    from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_prompt_execution_settings import (
        OpenAIChatPromptExecutionSettings,
    )

logger = logging.getLogger(__name__)


def update_settings_from_function_call_configuration(
    function_choice_configuration: "FunctionCallChoiceConfiguration",
    settings: "OpenAIChatPromptExecutionSettings",
    type: str,
) -> None:
    """Update the settings from a FunctionChoiceConfiguration."""
    if function_choice_configuration.available_functions:
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
<<<<<<< main
                "properties": {
                    param.name: param.schema_data for param in metadata.parameters
                },
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
>>>>>>> Stashed changes
=======
                "properties": {param.name: param.schema_data for param in metadata.parameters},
                "properties": {param.name: param.schema_data for param in metadata.parameters if param.is_required},
>>>>>>> origin/PR
                "required": [p.name for p in metadata.parameters if p.is_required],
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
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
                "properties": {param.name: param.schema_data for param in metadata.parameters},
                "properties": {param.name: param.schema_data for param in metadata.parameters if param.is_required},
                "required": [p.name for p in metadata.parameters if p.is_required],
=======
                "properties": {
                    param.name: param.schema_data for param in metadata.parameters if param.include_in_function_choices
                },
                "required": [p.name for p in metadata.parameters if p.is_required and p.include_in_function_choices],
>>>>>>> ms/feature-python-search
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
            },
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
                    raise ServiceInitializationError(
                        f"Values for filter key '{key}' are not lists."
                    )
        combined_filters[key] = list(combined_functions.keys())

    return combined_filters


def merge_function_results(
    messages: list[ChatMessageContent],
) -> list[ChatMessageContent]:
    """Combine multiple function result content types to one chat message content type.

    This method combines the FunctionResultContent items from separate ChatMessageContent messages,
    and is used in the event that the `context.terminate = True` condition is met.
    """
    items: list[Any] = []
    for message in messages:
        items.extend([item for item in message.items if isinstance(item, FunctionResultContent)])
    return [
        ChatMessageContent(
            role=AuthorRole.TOOL,
            items=items,
        )
    ]
