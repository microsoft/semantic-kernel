# Copyright (c) Microsoft. All rights reserved.

import re
from typing import Callable, Optional, Tuple
from xml.etree import ElementTree as ET

from semantic_kernel.kernel_exception import KernelException
from semantic_kernel.orchestration.context_variables import ContextVariables
from semantic_kernel.orchestration.sk_context import SKContext
from semantic_kernel.orchestration.sk_function_base import SKFunctionBase
from semantic_kernel.planning.plan import Plan
from semantic_kernel.planning.planning_exception import PlanningException

# Constants
GOAL_TAG = "goal"
SOLUTION_TAG = "plan"
FUNCTION_TAG = "function."
SET_CONTEXT_VARIABLE_TAG = "setContextVariable"
APPEND_TO_RESULT_TAG = "appendToResult"


class SequentialPlanParser:
    @staticmethod
    def get_skill_function(
        context: SKContext,
    ) -> Callable[[str, str], Optional[SKFunctionBase]]:
        def function(skill_name: str, function_name: str) -> Optional[SKFunctionBase]:
            try:
                return context.skills.get_function(skill_name, function_name)
            except KernelException:
                return None

        return function

    @staticmethod
    def to_plan_from_xml(
        xml_string: str,
        goal: str,
        get_skill_function: Callable[[str, str], Optional[SKFunctionBase]],
        allow_missing_functions: bool = False,
    ):
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
                    raise PlanningException(
                        PlanningException.ErrorCodes.InvalidPlan,
                        f"Failed to parse plan xml strings: '{xml_string}' or '{plan_xml}'",
                    )
            else:
                raise PlanningException(
                    PlanningException.ErrorCodes.InvalidPlan,
                    f"Failed to parse plan xml string: '{xml_string}'",
                )

        solution = xml_doc.findall(".//" + SOLUTION_TAG)

        plan = Plan.from_goal(goal)
        for solution_node in solution:
            for child_node in solution_node:
                if child_node.tag == "#text" or child_node.tag == "#comment":
                    continue

                if child_node.tag.startswith(FUNCTION_TAG):
                    skill_function_name = child_node.tag.split(FUNCTION_TAG)[1]
                    (
                        skill_name,
                        function_name,
                    ) = SequentialPlanParser.get_skill_function_names(
                        skill_function_name
                    )

                    if function_name:
                        skill_function = get_skill_function(skill_name, function_name)

                        if skill_function is not None:
                            plan_step = Plan.from_function(skill_function)

                            function_variables = ContextVariables()
                            function_outputs = []
                            function_results = []

                            view = skill_function.describe()
                            for p in view.parameters:
                                function_variables.set(p.name, p.default_value)

                            for attr in child_node.attrib:
                                if attr == SET_CONTEXT_VARIABLE_TAG:
                                    function_outputs.append(child_node.attrib[attr])
                                elif attr == APPEND_TO_RESULT_TAG:
                                    function_outputs.append(child_node.attrib[attr])
                                    function_results.append(child_node.attrib[attr])
                                else:
                                    function_variables.set(
                                        attr, child_node.attrib[attr]
                                    )

                            plan_step._outputs = function_outputs
                            plan_step._parameters = function_variables

                            for result in function_results:
                                plan._outputs.append(result)

                            plan.add_steps([plan_step])
                        elif allow_missing_functions:
                            plan.add_steps([Plan.from_goal(skill_function_name)])
                        else:
                            raise PlanningException(
                                PlanningException.ErrorCodes.InvalidPlan,
                                f"Failed to find function '{skill_function_name}' in skill '{skill_name}'.",
                            )

        return plan

    @staticmethod
    def get_skill_function_names(skill_function_name: str) -> Tuple[str, str]:
        skill_function_name_parts = skill_function_name.split(".")
        skill_name = (
            skill_function_name_parts[0] if len(skill_function_name_parts) > 0 else ""
        )
        function_name = (
            skill_function_name_parts[1]
            if len(skill_function_name_parts) > 1
            else skill_function_name
        )
        return skill_name, function_name
