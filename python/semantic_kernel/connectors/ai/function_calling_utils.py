# Copyright (c) Microsoft. All rights reserved.

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
    metadata: KernelFunctionMetadata,
) -> dict[str, Any]:
    """Convert the kernel function metadata to function calling format."""
    return {
        "type": "function",
        "function": {
            "name": metadata.fully_qualified_name,
            "description": metadata.description or "",
            "parameters": {
                "type": "object",
                "properties": {param.name: param.schema_data for param in metadata.parameters if param.is_required},
                "required": [p.name for p in metadata.parameters if p.is_required],
            },
        },
    }
