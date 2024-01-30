# Copyright (c) Microsoft. All rights reserved.

import json
import logging
from typing import Any, Dict, List, Optional, Tuple

from openai.types.chat import ChatCompletion

from semantic_kernel import Kernel, KernelContext
from semantic_kernel.connectors.ai.open_ai.models.chat.function_call import FunctionCall
from semantic_kernel.connectors.ai.open_ai.semantic_functions.open_ai_chat_prompt_template import (
    OpenAIChatPromptTemplate,
)
from semantic_kernel.orchestration.kernel_function_base import KernelFunctionBase

logger: logging.Logger = logging.getLogger(__name__)


def _describe_function(function: KernelFunctionBase) -> Dict[str, str]:
    """Create the object used for function_calling.

    Assumes that arguments for semantic functions are optional, for native functions required.
    """
    func_view = function.describe()
    return {
        "name": f"{func_view.plugin_name}-{func_view.name}",
        "description": func_view.description,
        "parameters": {
            "type": "object",
            "properties": {
                param.name: {"description": param.description, "type": param.type_} for param in func_view.parameters
            },
            "required": [p.name for p in func_view.parameters if p.required],
        },
    }


def get_function_calling_object(kernel: Kernel, filter: Dict[str, List[str]]) -> List[Dict[str, str]]:
    """Create the object used for function_calling.

    args:
        kernel: the kernel.
        filter: a dictionary with keys
            exclude_plugin, include_plugin, exclude_function, include_function
            and lists of the required filter.
            The function name should be in the format "plugin_name-function_name".
            Using exclude_plugin and include_plugin at the same time will raise an error.
            Using exclude_function and include_function at the same time will raise an error.
            If using include_* implies that all other function will be excluded.
            Example:
                filter = {
                    "exclude_plugin": ["plugin1", "plugin2"],
                    "include_function": ["plugin3-function1", "plugin4-function2"],
                    }
                will return only plugin3-function1 and plugin4-function2.
                filter = {
                    "exclude_function": ["plugin1-function1", "plugin2-function2"],
                    }
                will return all functions except plugin1-function1 and plugin2-function2.
        caller_function_name: the name of the function that is calling the other functions.
    returns:
        a filtered list of dictionaries of the functions in the kernel that can be passed to the function calling api.
    """
    include_plugin = filter.get("include_plugin", None)
    exclude_plugin = filter.get("exclude_plugin", [])
    include_function = filter.get("include_function", None)
    exclude_function = filter.get("exclude_function", [])
    if include_plugin and exclude_plugin:
        raise ValueError("Cannot use both include_plugin and exclude_plugin at the same time.")
    if include_function and exclude_function:
        raise ValueError("Cannot use both include_function and exclude_function at the same time.")
    if include_plugin:
        include_plugin = [plugin.lower() for plugin in include_plugin]
    if exclude_plugin:
        exclude_plugin = [plugin.lower() for plugin in exclude_plugin]
    if include_function:
        include_function = [function.lower() for function in include_function]
    if exclude_function:
        exclude_function = [function.lower() for function in exclude_function]
    result = []
    for (
        plugin_name,
        plugin,
    ) in kernel.plugins.data.items():
        if plugin_name in exclude_plugin or (include_plugin and plugin_name not in include_plugin):
            continue
        for function_name, function in plugin.items():
            current_name = f"{plugin_name}-{function_name}"
            if current_name in exclude_function or (include_function and current_name not in include_function):
                continue
            result.append(_describe_function(function))
    return result


async def execute_function_call(kernel: Kernel, function_call: FunctionCall, log: Optional[Any] = None) -> str:
    if log:
        logger.warning("The `log` parameter is deprecated. Please use the `logging` module instead.")
    result = await kernel.run(
        kernel.func(**function_call.split_name_dict()),
        input_vars=function_call.to_context_variables(),
    )
    logger.info(f"Function call result: {result}")
    return str(result)


async def chat_completion_with_function_call(
    kernel: Kernel,
    context: KernelContext,
    chat_plugin_name: Optional[str] = None,
    chat_function_name: Optional[str] = None,
    chat_function: Optional[KernelFunctionBase] = None,
    *,
    log: Optional[Any] = None,
    **kwargs: Dict[str, Any],
) -> KernelContext:
    """Perform a chat completion with auto-executing function calling.

    This is a recursive function that will execute the chat function multiple times,
    at least once to get a first completion, if a function_call is returned,
    the function_call is executed (using the execute_function_call method),
    the result is added to the chat prompt template and another completion is requested,
    by calling the function again, if it returns a function_call, it is executed again,
    until the maximum number of function calls is reached,
    at that time a final completion is done without functions.

    args:
        kernel: the kernel to use.
        context: the context to use.
        functions: the function calling object,
            make sure to use get_function_calling_object method to create it.
        Optional arguments:
            chat_plugin_name: the plugin name of the chat function.
            chat_function_name: the function name of the chat function.
            chat_function: the chat function, if not provided, it will be retrieved from the kernel.
                make sure to provide either the chat_function or the chat_plugin_name and chat_function_name.

            max_function_calls: the maximum number of function calls to execute, defaults to 5.
            current_call_count: the current number of function calls executed.

    returns:
        the context with the result of the chat completion, just like a regular invoke_async/run_async.
    """
    if log:
        logger.warning("The `log` parameter is deprecated. Please use the `logging` module instead.")
    # check the number of function calls
    max_function_calls = kwargs.get("max_function_calls", 5)
    current_call_count = kwargs.get("current_call_count", 0)
    # get the chat function
    if chat_function is None:
        chat_function = kernel.func(plugin_name=chat_plugin_name, function_name=chat_function_name)
    assert isinstance(
        chat_function._chat_prompt_template, OpenAIChatPromptTemplate
    ), "Please make sure to initialize your chat function with the OpenAIChatPromptTemplate class."
    settings = chat_function._chat_prompt_template.prompt_config.execution_settings
    if current_call_count >= max_function_calls:
        settings.functions = []
    context = await chat_function.invoke_async(
        context=context,
        # when the maximum number of function calls is reached, execute the chat function without Functions.
        settings=settings,
    )
    function_call = context.objects.pop("function_call", None)
    # if there is no function_call or if the content is not a FunctionCall object, return the context
    if function_call is None or not isinstance(function_call, FunctionCall):
        return context
    result = await execute_function_call(kernel, function_call)
    # add the result to the chat prompt template
    chat_function._chat_prompt_template.add_function_response_message(name=function_call.name, content=str(result))
    # request another completion
    return await chat_completion_with_function_call(
        kernel,
        chat_function=chat_function,
        context=context,
        max_function_calls=max_function_calls,
        current_call_count=current_call_count + 1,
    )


def _parse_message(
    message: ChatCompletion, with_data: bool = False
) -> Tuple[Optional[str], Optional[str], Optional[FunctionCall]]:
    """
    Parses the message.

    Arguments:
        message {OpenAIObject} -- The message to parse.

    Returns:
        Tuple[Optional[str], Optional[Dict]] -- The parsed message.
    """
    content = message.content if hasattr(message, "content") else None
    tool_calls = message.tool_calls if hasattr(message, "tool_calls") else None
    function_calls = (
        [FunctionCall(id=call.id, name=call.function.name, arguments=call.function.arguments) for call in tool_calls]
        if tool_calls
        else None
    )

    # todo: support multiple function calls
    function_call = function_calls[0] if function_calls else None

    if not with_data:
        return (content, None, function_call)
    else:
        tool_content = None
        if message.model_extra and "context" in message.model_extra:
            if "messages" in message.model_extra["context"]:
                for m in message.model_extra["context"]["messages"]:
                    if m.get("role") == "tool":
                        tool_content = m.get("content", None)
                        break
            else:
                tool_content = json.dumps(message.model_extra["context"])
        return (content, tool_content, function_call)


def _parse_choices(choice) -> Tuple[str, int]:
    message = ""
    if choice.delta.content:
        message += choice.delta.content

    return message, choice.index
