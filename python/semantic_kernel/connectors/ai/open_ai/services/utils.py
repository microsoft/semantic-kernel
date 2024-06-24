# Copyright (c) Microsoft. All rights reserved.
import logging
from typing import TYPE_CHECKING, Any

from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.function_call_behavior import (
        FunctionCallConfiguration,
    )
    from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_prompt_execution_settings import (
        OpenAIChatPromptExecutionSettings,
    )

logger = logging.getLogger(__name__)


def update_settings_from_function_call_configuration(
    function_call_configuration: "FunctionCallConfiguration",
    settings: "OpenAIChatPromptExecutionSettings",
) -> None:
    """Update the settings from a FunctionCallConfiguration."""
    if function_call_configuration.required_functions:
        if len(function_call_configuration.required_functions) > 1:
            logger.warning(
                "Multiple required functions are not supported. Using the first required function."
            )
        settings.tools = [
            kernel_function_metadata_to_openai_tool_format(
                function_call_configuration.required_functions[0]
            )
        ]
        settings.tool_choice = function_call_configuration.required_functions[
            0
        ].fully_qualified_name
        return
    if function_call_configuration.available_functions:
        settings.tool_choice = (
            "auto" if len(function_call_configuration.available_functions) > 0 else None
        )
        settings.tools = [
            kernel_function_metadata_to_openai_tool_format(f)
            for f in function_call_configuration.available_functions
        ]


def kernel_function_metadata_to_openai_tool_format(
    metadata: KernelFunctionMetadata,
) -> dict[str, Any]:
    """Convert the kernel function metadata to OpenAI format."""
    return {
        "type": "function",
        "function": {
            "name": metadata.fully_qualified_name,
            "description": metadata.description or "",
            "parameters": {
                "type": "object",
                "properties": {
                    param.name: param.schema_data for param in metadata.parameters
                },
                "required": [p.name for p in metadata.parameters if p.is_required],
            },
        },
    }
