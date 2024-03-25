# Copyright (c) Microsoft. All rights reserved.
from __future__ import annotations

import logging
from typing import Any

from semantic_kernel import Kernel
from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.functions.kernel_parameter_metadata import KernelParameterMetadata

logger: logging.Logger = logging.getLogger(__name__)


TYPE_MAPPER = {
    "str": "string",
    "int": "number",
    "float": "number",
    "bool": "boolean",
    "list": "array",
    "dict": "object",
}


def _describe_tool_call(function: KernelFunction) -> dict[str, Any]:
    """Create the object used for the tool call.

    Assumes that arguments for semantic functions are optional, for native functions required.
    """
    func_metadata = function.metadata
    params = [parse_param(p) for p in func_metadata.parameters]
    return {
        "type": "function",
        "function": {
            "name": func_metadata.fully_qualified_name,
            "description": func_metadata.description,
            "parameters": {
                "type": "object",
                "properties": {name: details for p in params for name, details in p.items()},
                "required": [p.name for p in func_metadata.parameters if p.is_required],
            },
        },
    }


def parse_param(param: KernelParameterMetadata) -> dict[str, str]:
    """Parse the parameter type."""
    details = {"description": param.description}
    details["type"] = parse_individual_param(param.type_)
    if hasattr(param, "enum"):
        details["enum"] = param.enum
    if "[" in param.type_:
        subtype = param.type_.split("[")[1].split("]")[0]
        details["items"] = {"type": parse_individual_param(subtype)}
    return {param.name: details}


def parse_individual_param(param_type: str | None) -> str:
    """Parse the parameter type."""
    if not param_type:
        return "string"
    if "[" in param_type:
        main_type = param_type.split("[")[0]
        return TYPE_MAPPER.get(main_type.lower(), "array")
    if "," in param_type:
        param_type = param_type.split(",", maxsplit=1)[0]
    return TYPE_MAPPER.get(param_type.lower(), "string")


def _describe_function(function: KernelFunction) -> dict[str, str]:
    """Create the object used for function_calling.
    Assumes that arguments for semantic functions are optional, for native functions required.
    """
    func_metadata = function.metadata
    return {
        "name": func_metadata.fully_qualified_name,
        "description": func_metadata.description,
        "parameters": {
            "type": "object",
            "properties": {
                param.name: {"description": param.description, "type": param.type_}
                for param in func_metadata.parameters
            },
            "required": [p.name for p in func_metadata.parameters if p.is_required],
        },
    }


def get_tool_call_object(kernel: Kernel, filter: dict[str, list[str]] = {}) -> list[dict[str, str]]:
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
    kernel: Kernel, filter: dict[str, list[str]] = {}, is_tool_call: bool | None = False
) -> list[dict[str, str]]:
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
        for function in plugin.functions.values():
            if function.fully_qualified_name in exclude_function or (
                include_function and function.fully_qualified_name not in include_function
            ):
                continue
            result.append(_describe_tool_call(function) if is_tool_call else _describe_function(function))
    return result
