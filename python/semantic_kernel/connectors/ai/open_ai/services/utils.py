# Copyright (c) Microsoft. All rights reserved.
import logging
from typing import TYPE_CHECKING

from semantic_kernel.connectors.utils.function_call_format import kernel_function_metadata_to_function_call_format

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
            kernel_function_metadata_to_function_call_format(
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
            kernel_function_metadata_to_function_call_format(f)
            for f in function_call_configuration.available_functions
        ]
