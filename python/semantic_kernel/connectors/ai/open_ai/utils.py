# Copyright (c) Microsoft. All rights reserved.

import json
import logging
from typing import Any, Dict, List, Optional, Tuple, Union

from openai.types.chat import ChatCompletion

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.open_ai.models.chat_completion.function_call import FunctionCall
from semantic_kernel.connectors.ai.open_ai.models.chat_completion.tool_calls import ToolCall
from semantic_kernel.connectors.ai.text_completion_client_base import TextCompletionClientBase
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.functions.function_result import FunctionResult
from semantic_kernel.functions.kernel_arguments import KernelArguments
import logging
from typing import Dict, List, Optional

from semantic_kernel import Kernel
from semantic_kernel.functions.kernel_function import KernelFunction

logger: logging.Logger = logging.getLogger(__name__)


TYPE_MAPPER = {
    "str": "string",
    "int": "number",
    "float": "number",
    "bool": "boolean",
    "list": "array",
    "dict": "object",
}


def _describe_tool_call(function: KernelFunction) -> Dict[str, str]:
    """Create the object used for the tool call.

    Assumes that arguments for semantic functions are optional, for native functions required.
    """
    func_view = function.metadata
    return {
        "type": "function",
        "function": {
            "name": f"{func_view.plugin_name}-{func_view.name}",
            "description": func_view.description,
    func_metadata = function.metadata
    return {
        "type": "function",
        "function": {
            "name": f"{func_metadata.plugin_name}-{func_metadata.name}",
            "description": func_metadata.description,
            "parameters": {
                "type": "object",
                "properties": {
                    param.name: {
                        "description": param.description,
                        "type": parse_param(param.type_),
                        **({"enum": param.enum} if hasattr(param, "enum") else {}),  # Added support for enum
                    }
                    for param in func_view.parameters
                    if param.expose
                },
                "required": [p.name for p in func_view.parameters if p.required and p.expose],
                    for param in func_metadata.parameters
                },
                "required": [p.name for p in func_metadata.parameters if p.is_required],
            },
        },
    }


def parse_param(param_type: Optional[str]) -> str:
    """Parse the parameter type."""
    if not param_type:
        return "string"
    if "," in param_type:
        param_type = param_type.split(",", maxsplit=1)[0]
    return TYPE_MAPPER.get(param_type, "string")


def _describe_function(function: KernelFunction) -> Dict[str, str]:
    """Create the object used for function_calling.
    Assumes that arguments for semantic functions are optional, for native functions required.
    """
    func_view = function.metadata
    return {
        "name": f"{func_view.plugin_name}-{func_view.name}",
        "description": func_view.description,
    func_metadata = function.metadata
    return {
        "name": f"{func_metadata.plugin_name}-{func_metadata.name}",
        "description": func_metadata.description,
        "parameters": {
            "type": "object",
            "properties": {
                param.name: {"description": param.description, "type": param.type_}
                for param in func_view.parameters
                if param.expose
            },
            "required": [p.name for p in func_view.parameters if p.required],
                for param in func_metadata.parameters
            },
            "required": [p.name for p in func_metadata.parameters if p.is_required],
        },
    }


def get_tool_call_object(kernel: Kernel, filter: Dict[str, List[str]]) -> List[Dict[str, str]]:
    """Create the object used for a tool call.

    This is the preferred method to create the tool call object.

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
    returns:
        a filtered list of dictionaries of the functions in the kernel that can be passed to the function calling api.
    """
    return get_function_calling_object(kernel, filter, is_tool_call=True)


def get_function_calling_object(
    kernel: Kernel, filter: Dict[str, List[str]], is_tool_call: Optional[bool] = False
) -> List[Dict[str, str]]:
    """Create the object used for a function call.

    Note: although Azure has deprecated function calling, SK still supports it for the time being.

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
        is_tool_call: if True, the function will return a list of tool calls, otherwise a list of functions.
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
        include_plugin = [plugin for plugin in include_plugin]
    if exclude_plugin:
        exclude_plugin = [plugin for plugin in exclude_plugin]
    if include_function:
        include_function = [function for function in include_function]
    if exclude_function:
        exclude_function = [function for function in exclude_function]
    result = []
    for (
        plugin_name,
        plugin,
    ) in kernel.plugins.plugins.items():
        if plugin_name in exclude_plugin or (include_plugin and plugin_name not in include_plugin):
            continue
        for function_name, function in plugin.functions.items():
            current_name = f"{plugin_name}-{function_name}"
            if current_name in exclude_function or (include_function and current_name not in include_function):
                continue
            result.append(_describe_tool_call(function) if is_tool_call else _describe_function(function))
    return result


async def execute(kernel: Kernel, func: KernelFunction, arguments: KernelArguments) -> FunctionResult:
    """Execute a function and return the result.

    Args:
        kernel: the kernel to use.
        func: the function to execute.
        arguments: the arguments to pass to the function.

    Returns:
        str: the result of the execution.
    """
    result = await kernel.invoke(functions=func, arguments=arguments)
    logger.info(f"Execution result: {result}")
    return result


async def execute_function_call(kernel: Kernel, function_call: FunctionCall) -> FunctionResult:
    """Execute a function call and return the result."""
    func = kernel.func(**function_call.split_name_dict())
    arguments = function_call.to_kernel_arguments()
    return await execute(kernel, func, arguments)


async def execute_and_store_tool_call(
    kernel: Kernel,
    tool_call: ToolCall,
    chat_function: KernelFunction,
):
    """Execute a tool call and store the result in the chat prompt template."""
    tool_call_result = await execute_tool_call(kernel, tool_call)
    chat_function.chat_prompt_template.add_function_response_message(
        name=tool_call.function.name, content=str(tool_call_result), tool_call_id=tool_call.id
    )


async def execute_tool_call(kernel: Kernel, tool_call: ToolCall) -> FunctionResult:
    """Execute a tool call and return the result."""
    func = kernel.func(**tool_call.function.split_name_dict())
    arguments = tool_call.function.to_kernel_arguments()
    return await execute(kernel, func, arguments)


async def chat_completion_with_tool_call(
    kernel: Kernel,
    arguments: Optional[KernelArguments] = None,
    chat_plugin_name: Optional[str] = None,
    chat_function_name: Optional[str] = None,
    chat_function: Optional[KernelFunction] = None,
    chat_history: Optional[ChatHistory] = None,
    **kwargs: Dict[str, Any],
) -> FunctionResult:
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
        arguments: the arguments to pass to the chat function.
    Optional arguments:
        chat_plugin_name: the plugin name of the chat function.
        chat_function_name: the function name of the chat function.
        chat_function: the chat function, if not provided, it will be retrieved from the kernel.
            make sure to provide either the chat_function or the chat_plugin_name and chat_function_name.
        chat_history: the chat history to use, if not provided, will attempt to retrieve from arguments
            with key "chat_history".

        max_function_calls: the maximum number of function calls to execute, defaults to 5.
        current_call_count: the current number of function calls executed.

    returns:
        the FunctionResult with the result of the chat completion, just like a regular invoke/run_async.
    """

    chat_history or arguments["chat_history"]

    # check the number of function calls
    max_function_calls = kwargs.get("max_function_calls", 5)
    current_call_count = kwargs.get("current_call_count", 0)
    # get the chat function
    if chat_function is None:
        if chat_plugin_name is None or chat_function_name is None:
            raise ValueError("Please provide either the chat_function or the chat_plugin_name and chat_function_name.")
        chat_function = kernel.func(plugin_name=chat_plugin_name, function_name=chat_function_name)
    assert issubclass(
        type(chat_function.ai_service), Union[ChatCompletionClientBase, TextCompletionClientBase]
    ), "Please make sure to initialize your chat function with the OpenAIChatPromptTemplate class."

    settings = chat_function.prompt_execution_settings[chat_function.ai_service.service_id]

    if not arguments:
        arguments = KernelArguments()
    arguments.execution_settings[settings.service_id] = settings
    arguments["user_input"] = ("\n").join([f"{msg.role}: {msg.content}" for msg in chat_history])
    if current_call_count >= max_function_calls:
        settings.functions = []
    result = await chat_function.invoke(
        kernel=kernel,
        arguments=arguments,
        # when the maximum number of function calls is reached, execute the chat function without Functions.
    )
    if not isinstance(result, FunctionResult) and result.value[0].tool_call is None:
        return result
    function_call = next(
        (
            fc
            for fc in (result.value[0].function_call or result.value[0].tool_calls or [None])
            if isinstance(fc, (FunctionCall, ToolCall))
        ),
        None,
    )
    if function_call:
        execute_call = execute_tool_call if isinstance(function_call, ToolCall) else execute_function_call
        result = await execute_call(kernel, function_call)
        tool_call_id = function_call.id
    else:
        return result
    # add the result to the chat prompt template
    chat_history.add_tool_message()
    chat_function.chat_prompt_template.add_function_response_message(
        name=function_call.function.name, content=str(result), tool_call_id=tool_call_id
    )
    # request another completion
    return await chat_completion_with_tool_call(
        kernel,
        arguments=arguments,
        chat_function=chat_function,
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
