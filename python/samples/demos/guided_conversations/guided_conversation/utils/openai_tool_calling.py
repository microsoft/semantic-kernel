# Copyright (c) Microsoft. All rights reserved.

from dataclasses import dataclass
from enum import Enum
import json
import logging
from typing import Any

from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.functions import FunctionResult

logger = logging.getLogger(__name__)


@dataclass
class ToolArg:
    argument_name: str
    required: bool


@dataclass
class Tool:
    name: str
    args: list[ToolArg]


class ToolValidationResult(Enum):
    NO_TOOL_CALLED = "No tool was called"
    INVALID_TOOL_CALLED = "A tool was called with an unexpected name"
    MISSING_REQUIRED_ARGUMENT = "The tool called is missing a required argument"
    INVALID_ARGUMENT_TYPE = "The value of an argument is of an unexpected type"
    SUCCESS = "success"


def parse_function_result(response: FunctionResult) -> dict[str, Any]:
    """Parse the response from SK's FunctionResult object into only the relevant data for easier downstream processing.
    This should only be used when you expect the response to contain tool calls.

    Args:
        response (FunctionResult): The response from the kernel.

    Returns:
        dict[str, Any]: The parsed response data with the following format if n was set greater than 1:
        {
            "choices": [
                {
                    "tool_names": list[str],
                    "tool_args_list": list[dict[str, Any]],
                    "message": str,
                    "finish_reason": str,
                    "validation_result": ToolValidationResult
                }, ...
            ]
        }
        Otherwise, the response will directly contain the data from the first choice (tool_names, etc keys)
    """
    response_data: dict[str, Any] = {"choices": []}
    for response_choice in response.value:
        response_data_curr = {}
        finish_reason = response_choice.finish_reason

        if finish_reason == "tool_calls":
            tool_names = []
            tool_args_list = []
            # Only look at the items that are of instance `FunctionCallContent`
            tool_calls = [item for item in response_choice.items if isinstance(item, FunctionCallContent)]
            for tool_call in tool_calls:
                if "-" not in tool_call.name:
                    logger.info(f"Tool call name {tool_call.name} does not match naming convention - modifying name.")
                    tool_names.append(tool_call.name + "-" + tool_call.name)
                else:
                    tool_names.append(tool_call.name)
                try:
                    tool_args = json.loads(tool_call.arguments)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse tool arguments for tool call {tool_call.name}. Using empty dict.")
                    tool_args = {}
                tool_args_list.append(tool_args)
            response_data_curr["tool_names"] = tool_names
            response_data_curr["tool_args_list"] = tool_args_list

        response_data_curr["message"] = response_choice.content
        response_data_curr["finish_reason"] = finish_reason
        response_data["choices"].append(response_data_curr)

    if len(response_data["choices"]) == 1:
        response_data.update(response_data["choices"][0])
        del response_data["choices"]

    return response_data


def construct_tool_objects(kernel_function_tools: dict) -> list[Tool]:
    """Construct a list of Tool objects from the kernel function tools definition.

    Args:
        kernel_function_tools (dict): The definition of tools done by the kernel function.

    Returns:
        list[Tool]: The list of Tool objects constructed from the kernel function tools definition.
    """

    tool_objects: list[Tool] = []
    for tool_definition in kernel_function_tools:
        tool_name = tool_definition["function"]["name"]
        tool_args = tool_definition["function"]["parameters"]["properties"]

        tool_arg_objects: list[ToolArg] = []
        for argument_name, _ in tool_args.items():
            tool_arg = ToolArg(argument_name=argument_name, required=False)
            tool_arg_objects.append(tool_arg)

        required_args = tool_definition["function"]["parameters"]["required"]
        for tool_arg_object in tool_arg_objects:
            if tool_arg_object.argument_name in required_args:
                tool_arg_object.required = True

        tool_objects.append(Tool(name=tool_name, args=tool_arg_objects))
    return tool_objects


def validate_tool_calling(response: dict[str, Any], request_tool_param: dict) -> ToolValidationResult:
    """Validate that the response from the LLM called tools corrected.
    1. Check if any tool was called.
    2. Check if the tools called were valid (names match)
    3. Check if all the required arguments were passed.

    Args:
        response (dict[str, Any]): The response from the LLM containing the tools called (output of parse_function_result)
        tools (list[Tool]): The list of tools that can be called by the model.

    Returns:
        ToolValidationResult: The result of the validation. ToolValidationResult.SUCCESS if the validation passed.
    """

    tool_objects = construct_tool_objects(request_tool_param)
    tool_names = response.get("tool_names", [])
    tool_args_list = response.get("tool_args_list", [])

    # Check if any tool was called.
    if not tool_names:
        logger.info("No tool was called.")
        return ToolValidationResult.NO_TOOL_CALLED

    for tool_name, tool_args in zip(tool_names, tool_args_list, strict=True):
        # Check the tool names is valid.
        tool: Tool | None = next((t for t in tool_objects if t.name == tool_name), None)
        if not tool:
            logger.warning(f"Invalid tool called: {tool_name}")
            return ToolValidationResult.INVALID_TOOL_CALLED

        for arg in tool.args:
            # Check if the required arguments were passed.
            if arg.required and arg.argument_name not in tool_args:
                logger.warning(f"Missing required argument '{arg.argument_name}' for tool '{tool_name}'.")
                return ToolValidationResult.MISSING_REQUIRED_ARGUMENT

    return ToolValidationResult.SUCCESS
