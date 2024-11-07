# Copyright (c) Microsoft. All rights reserved.

from dataclasses import dataclass

from pydantic import ValidationError
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.function_calling_utils import kernel_function_metadata_to_function_call_format
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents import ChatMessageContent
from semantic_kernel.functions import KernelArguments

from guided_conversation.utils.openai_tool_calling import parse_function_result, validate_tool_calling


@dataclass
class PluginOutput:
    """A wrapper for all Guided Conversation Plugins. This class is used to return the output of a generic plugin.

    Args:
        update_successful (bool): Whether the update was successful.
        messages (list[ChatMessageContent]): A list of messages to be used at the user's digression, it
        contains information about the process of calling the plugin.
    """

    update_successful: bool
    messages: list[ChatMessageContent]


def format_kernel_functions_as_tools(kernel: Kernel, functions: list[str]):
    """Format kernel functions as JSON schemas for custom validation."""
    formatted_tools = []
    for _, kernel_plugin_def in kernel.plugins.items():
        for function_name, function_def in kernel_plugin_def.functions.items():
            if function_name in functions:
                func_metadata = function_def.metadata
                formatted_tools.append(kernel_function_metadata_to_function_call_format(func_metadata))
    return formatted_tools


async def fix_error(
    kernel: Kernel, prompt_template: str, req_settings: AzureChatCompletion, arguments: KernelArguments
) -> dict:
    """Invokes the error correction plugin. If a plugin is called & fails during execution, this function will retry
    the plugin. At a high level, we recommend the following steps when calling a plugin:
    1. Call the plugin.
    2. Parse the response.
    3. Validate the response.
    4. If the response is invalid (Validation or Value Error), retry the plugin by calling *this function*. For best
    results, check out plugins/agenda.py or plugins/artifact.py for examples of prompt templates & corresponding
    tools (which should be passed in the req_settings object). This function will handle the retry logic for you.

    Args:
        kernel (Kernel): The kernel object.
        prompt_template (str): The prompt template for the plugin.
        req_settings (AzureChatCompletion): The prompt execution settings.
        arguments (KernelArguments): The kernel arguments.

    Returns:
        dict: The result of the plugin call.
    """
    kernel_function_obj = kernel.add_function(
        prompt=prompt_template,
        function_name="error_correction",
        plugin_name="error_correction",
        template_format="handlebars",
        prompt_execution_settings=req_settings,
    )

    result = await kernel.invoke(function=kernel_function_obj, arguments=arguments)
    parsed_result = parse_function_result(result)

    formatted_tools = []
    for _, kernel_plugin_def in kernel.plugins.items():
        for _, function_def in kernel_plugin_def.functions.items():
            func_metadata = function_def.metadata
            formatted_tools.append(kernel_function_metadata_to_function_call_format(func_metadata))

    # Add any tools from req_settings
    if req_settings.tools:
        formatted_tools.extend(req_settings.tools)

    validation_result = validate_tool_calling(parsed_result, formatted_tools)
    parsed_result["validation_result"] = validation_result
    return parsed_result


def update_attempts(error: Exception, attempt_id: str, previous_attempts: list) -> str:
    """
    Updates the plugin class attribute list of previous attempts with the current attempt and error message
    (including duplicates).

    Args:
        error (Exception): The error object.
        attempt_id (str): The ID of the current attempt.
        previous_attempts (list): The list of previous attempts.

    Returns:
        str: A formatted (optimized for LLM performance) string of previous attempts, with duplicates removed.
    """
    if isinstance(error, ValidationError):
        error_str = "; ".join([e.get("msg") for e in error.errors()])
        # replace "; Input should be 'Unanswered'" with " or input should be 'Unanswered'" for clarity
        error_str = error_str.replace("; Input should be 'Unanswered'", " or input should be 'Unanswered'")
    else:
        error_str = str(error)
    new_failed_attempt = (attempt_id, error_str)
    previous_attempts.append(new_failed_attempt)

    # Format previous attempts to be more friendly for the LLM
    attempts_list = []
    unique_attempts = set(previous_attempts)
    for attempt, error in unique_attempts:
        attempts_list.append(f"Attempt: {attempt}\nError: {error}")
    llm_formatted_attempts = "\n".join(attempts_list)

    return previous_attempts, llm_formatted_attempts
