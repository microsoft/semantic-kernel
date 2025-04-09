# Copyright (c) Microsoft. All rights reserved.

import re
from collections.abc import Callable

from defusedxml import ElementTree as ET

from semantic_kernel.exceptions import PlannerInvalidPlanError
from semantic_kernel.exceptions.kernel_exceptions import KernelFunctionNotFoundError, KernelPluginNotFoundError
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.kernel import Kernel
from semantic_kernel.planners.plan import Plan

# Constants
GOAL_TAG = "goal"
SOLUTION_TAG = "plan"
FUNCTION_TAG = "function."
SET_CONTEXT_VARIABLE_TAG = "setContextVariable"
APPEND_TO_RESULT_TAG = "appendToResult"


class SequentialPlanParser:
    """Parser for Sequential planners."""

    @staticmethod
    def to_plan_from_xml(
        xml_string: str,
        goal: str,
        kernel: Kernel,
        get_plugin_function: Callable[[str, str], KernelFunction | None] | None = None,
        allow_missing_functions: bool = False,
    ):
        """Convert an xml string to a plan."""
        xml_string = "<xml>" + xml_string + "</xml>"
        try:
            xml_doc = ET.fromstring(xml_string)
        except ET.ParseError:
            # Attempt to parse <plan> out of it
            plan_regex = re.compile(r"<plan\b[^>]*>(.*?)</plan>", re.DOTALL)
            match = plan_regex.search(xml_string)

            if match:
                plan_xml = match.group(0)
                try:
                    xml_doc = ET.fromstring("<xml>" + plan_xml + "</xml>")
                except ET.ParseError:
                    raise PlannerInvalidPlanError(f"Failed to parse plan xml strings: '{xml_string}' or '{plan_xml}'")
            else:
                raise PlannerInvalidPlanError(f"Failed to parse plan xml string: '{xml_string}'")

        solution = xml_doc.findall(".//" + SOLUTION_TAG)

        plan = Plan.from_goal(goal)
        for solution_node in solution:
            for child_node in solution_node:
                if (
                    child_node.tag == "#text"
                    or child_node.tag == "#comment"
                    or (not child_node.tag.startswith(FUNCTION_TAG))
                ):
                    continue

                plugin_function_name = child_node.tag.split(FUNCTION_TAG)[1]
                if get_plugin_function:
                    try:
                        func = get_plugin_function(
                            *SequentialPlanParser.get_plugin_function_names(plugin_function_name)
                        )
                    except Exception as exc:
                        if allow_missing_functions:
                            plan.add_steps([Plan.from_goal(plugin_function_name)])
                            continue
                        raise PlannerInvalidPlanError(f"Failed to find function '{plugin_function_name}'.") from exc
                else:
                    try:
                        func = kernel.get_function_from_fully_qualified_function_name(plugin_function_name)
                    except (KernelFunctionNotFoundError, KernelPluginNotFoundError) as exc:
                        if allow_missing_functions:
                            plan.add_steps([Plan.from_goal(plugin_function_name)])
                            continue
                        raise PlannerInvalidPlanError(
                            f"Failed to find function '{plugin_function_name}'.",
                        ) from exc

                plan_step = Plan.from_function(func)

                function_variables = KernelArguments()
                function_outputs = []
                function_results = []

                for p in func.metadata.parameters:
                    function_variables[p.name] = p.default_value

                for attr in child_node.attrib:
                    if attr == SET_CONTEXT_VARIABLE_TAG:
                        function_outputs.append(child_node.attrib[attr])
                    elif attr == APPEND_TO_RESULT_TAG:
                        function_outputs.append(child_node.attrib[attr])
                        function_results.append(child_node.attrib[attr])
                    else:
                        function_variables[attr] = child_node.attrib[attr]

                plan_step._outputs = function_outputs
                plan_step._parameters = function_variables

                for result in function_results:
                    plan._outputs.append(result)

                plan.add_steps([plan_step])

        return plan

    @staticmethod
    def get_plugin_function_names(plugin_function_name: str) -> tuple[str, str]:
        """Get the plugin and function names from the plugin function name."""
        plugin_function_name_parts = plugin_function_name.split("-")
        plugin_name = plugin_function_name_parts[0] if len(plugin_function_name_parts) > 0 else ""
        function_name = plugin_function_name_parts[1] if len(plugin_function_name_parts) > 1 else plugin_function_name
        return plugin_name, function_name
