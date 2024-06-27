# Copyright (c) Microsoft. All rights reserved.

import logging
from copy import copy
from typing import TYPE_CHECKING, Any

from semantic_kernel.connectors.ai.function_choice_behavior import (
    FunctionChoiceBehavior,
)
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_prompt_execution_settings import (
    OpenAIChatPromptExecutionSettings,
)
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.exceptions import (
    FunctionCallInvalidArgumentsException,
    FunctionExecutionException,
)
from semantic_kernel.filters.auto_function_invocation.auto_function_invocation_context import (
    AutoFunctionInvocationContext,
)
from semantic_kernel.filters.filter_types import FilterTypes
from semantic_kernel.filters.kernel_filters_extension import _rebuild_auto_function_invocation_context
from semantic_kernel.functions.function_result import FunctionResult
from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.function_choice_behavior import (
        FunctionCallChoiceConfiguration,
    )
    from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_prompt_execution_settings import (
        OpenAIChatPromptExecutionSettings,
    )
    from semantic_kernel.functions.kernel_arguments import KernelArguments
    from semantic_kernel.kernel import Kernel

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


async def process_function_call(
    function_call: FunctionCallContent,
    chat_history: ChatHistory,
    kernel: "Kernel",
    arguments: "KernelArguments",
    function_call_count: int,
    request_index: int,
    function_behavior: FunctionChoiceBehavior,
) -> "AutoFunctionInvocationContext | None":
    """Processes the provided FunctionCallContent and updates the chat history."""
    args_cloned = copy(arguments)
    try:
        parsed_args = function_call.parse_arguments()
        if parsed_args:
            args_cloned.update(parsed_args)
    except (FunctionCallInvalidArgumentsException, TypeError) as exc:
        logger.info(f"Received invalid arguments for function {function_call.name}: {exc}. Trying tool call again.")
        frc = FunctionResultContent.from_function_call_content_and_result(
            function_call_content=function_call,
            result="The tool call arguments are malformed. Arguments must be in JSON format. Please try again.",
        )
        chat_history.add_message(message=frc.to_chat_message_content())
        return None

    try:
        if function_call.name is None:
            raise FunctionExecutionException("The function name is required.")
        if (
            function_behavior.function_fully_qualified_names
            and function_call.name not in function_behavior.function_fully_qualified_names
        ):
            raise FunctionExecutionException(
                f"Only functions: {function_behavior.function_fully_qualified_names} "
                f"are allowed, {function_call.name} is not allowed."
            )
        if function_behavior.filters:
            allowed_functions = [
                func.fully_qualified_name for func in kernel.get_list_of_function_metadata(function_behavior.filters)
            ]
            if function_call.name not in allowed_functions:
                raise FunctionExecutionException(
                    f"Only functions: {allowed_functions} are allowed, {function_call.name} is not allowed."
                )
        function_to_call = kernel.get_function(function_call.plugin_name, function_call.function_name)
    except Exception as exc:
        logger.exception(f"The function `{function_call.name}` is not part of the provided functions: {exc}.")
        frc = FunctionResultContent.from_function_call_content_and_result(
            function_call_content=function_call,
            result=(
                f"The tool call with name `{function_call.name}` is not part of the provided tools, "
                "please try again with a supplied tool call name and make sure to validate the name."
            ),
        )
        chat_history.add_message(message=frc.to_chat_message_content())
        return None

    num_required_func_params = len([param for param in function_to_call.parameters if param.is_required])
    if len(parsed_args) < num_required_func_params:
        msg = (
            f"There are `{num_required_func_params}` tool call arguments required and "
            f"only `{len(parsed_args)}` received. The required arguments are: "
            f"{[param.name for param in function_to_call.parameters if param.is_required]}. "
            "Please provide the required arguments and try again."
        )
        logger.info(msg)
        frc = FunctionResultContent.from_function_call_content_and_result(
            function_call_content=function_call,
            result=msg,
        )
        chat_history.add_message(message=frc.to_chat_message_content())
        return None

    logger.info(f"Calling {function_call.name} function with args: {function_call.arguments}")

    _rebuild_auto_function_invocation_context()
    invocation_context = AutoFunctionInvocationContext(
        function=function_to_call,
        kernel=kernel,
        arguments=args_cloned,
        chat_history=chat_history,
        function_result=FunctionResult(function=function_to_call.metadata, value=None),
        function_count=function_call_count,
        request_sequence_index=request_index,
    )
    if function_call.index is not None:
        invocation_context.function_sequence_index = function_call.index

    stack = kernel.construct_call_stack(
        filter_type=FilterTypes.AUTO_FUNCTION_INVOCATION,
        inner_function=_inner_auto_function_invoke_handler,
    )
    await stack(invocation_context)

    if invocation_context.terminate:
        return invocation_context

    frc = FunctionResultContent.from_function_call_content_and_result(
        function_call_content=function_call, result=invocation_context.function_result
    )
    chat_history.add_message(message=frc.to_chat_message_content())
    return None


async def _inner_auto_function_invoke_handler(context: AutoFunctionInvocationContext):
    """Inner auto function invocation handler."""
    try:
        result = await context.function.invoke(context.kernel, context.arguments)
        if result:
            context.function_result = result
    except Exception as exc:
        logger.exception(f"Error invoking function {context.function.fully_qualified_name}: {exc}.")
        value = f"An error occurred while invoking the function {context.function.fully_qualified_name}: {exc}"
        if context.function_result is not None:
            context.function_result.value = value
        else:
            context.function_result = FunctionResult(function=context.function.metadata, value=value)
        return
