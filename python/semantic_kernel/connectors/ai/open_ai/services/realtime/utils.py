# Copyright (c) Microsoft. All rights reserved.

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.function_choice_behavior import (
        FunctionCallChoiceConfiguration,
        FunctionChoiceType,
    )
    from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
    from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata


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
