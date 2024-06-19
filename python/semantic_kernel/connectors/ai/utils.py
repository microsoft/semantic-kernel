# Copyright (c) Microsoft. All rights reserved.

import logging
from typing import TYPE_CHECKING

from semantic_kernel.connectors.utils.function_call_format import kernel_function_metadata_to_function_call_format

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
    if function_choice_configuration.required_functions:
        settings.tool_choice = type
        settings.tools = [
            kernel_function_metadata_to_function_call_format(f)
            for f in function_choice_configuration.required_functions
        ]
    if function_choice_configuration.available_functions:
        settings.tool_choice = type
        settings.tools = [
            kernel_function_metadata_to_function_call_format(f)
            for f in function_choice_configuration.available_functions
        ]
