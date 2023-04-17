import logging
import re
import xml.etree.ElementTree as ET
from io import StringIO
from typing import List, Tuple

from semantic_kernel.diagnostics.verify import Verify
from semantic_kernel.kernel import Kernel
from semantic_kernel.orchestration.context_variables import ContextVariables
from semantic_kernel.orchestration.sk_context import SKContext
from semantic_kernel.planning.plan import Plan
from semantic_kernel.planning.planning_exception import (PlanningErrorCode,
                                                         PlanningException)


# Executes XML plans created by the Function Flow semantic function.
class FunctionFlowRunner:
    # The tag name used in the plan xml for the user's goal/ask.
    GOAL_TAG = "goal"

    # The tag name used in the plan xml for the solution.
    SOLUTION_TAG = "plan"

    # The tag name used in the plan xml for a step that calls a skill function.
    FUNCTION_TAG = "function."

    # The attribute tag used in the plan xml for setting the context variable name to set the output of a function to.
    SET_CONTEXT_VARIABLE_TAG = "setContextVariable"

    # The attribute tag used in the plan xml for appending the output of a function to the final result for a plan.
    APPEND_TO_RESULT_TAG = "appendToResult"

    def __init__(self, kernel: Kernel):
        self.kernel = kernel

    async def execute_xml_plan_async(
        self, context: SKContext, plan_payload: str
    ) -> SKContext:
        try:
            try:
                xmlDoc = ET.fromstring(f"<xml>{plan_payload}</xml>")
            except Exception as e:
                raise PlanningException(
                    PlanningErrorCode.INVALID_PLAN, "Failed to parse plan xml.", e
                )

            # Get the Goal
            goal_txt, goal_xml_string = self.gather_goal(xmlDoc)

            # Get the Solution
            solution = xmlDoc.findall(self.SOLUTION_TAG)

            # Prepare content for the new plan xml
            solution_content = StringIO()
            solution_content.write(f"<{self.SOLUTION_TAG}>\n")

            # Use goal as default function {{INPUT}} -- check and see if it's a plan in Input, if so, use goalTxt, otherwise, use the input.
            if not context.variables.get("PLAN__INPUT")[0]:
                try:
                    plan = Plan.from_json(str(context.variables))
                    plan_input = str(context.variables) if not plan.goal else goal_txt
                except Exception as e:
                    plan_input = str(context.variables)
            else:
                plan_input = context.variables["PLAN__INPUT"]

            function_input = plan_input if plan_input else goal_txt

            #
            # Process Solution nodes
            #
            logging.debug("Processing solution")

            # Process the solution nodes
            step_results = await self.process_node_list_async(
                solution, function_input, context
            )

            # Add the solution and variable updates to the new plan xml
            solution_content.write(f"{step_results}\n")
            solution_content.write(f"</{self.SOLUTION_TAG}>")

            # Update the plan xml
            solution_content_formatted = (
                solution_content.getvalue().replace("\r\n", "\n").strip()
            )
            updated_plan = f"""{goal_xml_string}{solution_content_formatted}"""
            context.variables[Plan.PLAN_KEY] = updated_plan
            context.variables["PLAN__INPUT"] = str(context.variables)

            return context

        except Exception as e:
            logging.error("Plan execution failed")
            raise

    async def process_node_list_async(
        self, node_list: List[ET.Element], function_input: str, context: SKContext
    ) -> str:
        step_and_text_results = []
        process_functions = True
        indent = "  "

        for o in node_list:
            parent_node_name = o.tag
            context.log.info("{0}: found node".format(parent_node_name))

            for o2 in o:
                if o2.tag == "#text":
                    context.log.info(
                        "{0}: appending text node".format(parent_node_name)
                    )
                    if o2.text is not None:
                        step_and_text_results.append(o2.text.strip())
                    continue

                if o2.tag.lower().startswith(self.FUNCTION_TAG.lower()):
                    skill_function_name = (
                        o2.tag.split(self.FUNCTION_TAG)[1]
                        if len(o2.tag.split(self.FUNCTION_TAG)) > 1
                        else ""
                    )
                    context.log.info(
                        "{0}: found skill node {1}".format(
                            parent_node_name, skill_function_name
                        )
                    )
                    skill_name, function_name = self.get_skill_function_names(
                        skill_function_name
                    )

                    if (
                        process_functions
                        and function_name
                        and context.is_function_registered(skill_name, function_name)
                    ):
                        Verify.not_null(function_name, "function_name")
                        skill_function = context.func(skill_name, function_name)
                        Verify.not_null(skill_function, "skill_function")

                        context.log.info(
                            "{0}: processing function {1}.{2}".format(
                                parent_node_name, skill_name, function_name
                            )
                        )

                        function_variables = ContextVariables(function_input)
                        variable_target_name = ""
                        append_to_result_name = ""

                        if o2.attrib:
                            for attr_name, attr_value in o2.attrib.items():
                                context.log.info(
                                    "{0}: processing attribute {1}".format(
                                        parent_node_name, attr_value
                                    )
                                )
                                if attr_value.startswith("$", 0, 1):
                                    # split attribute value by comma or semicolon
                                    attr_values = re.split(",|;", attr_value)

                                    if attr_values:
                                        attr_value_list = []

                                        for attr_val in attr_values:
                                            (
                                                attr_val_is_available,
                                                _,
                                            ) = context.variables.get(attr_val[1:])
                                            if attr_val_is_available:
                                                attr_value_list.append(
                                                    context.variables[attr_val[1:]]
                                                )

                                        if attr_value_list:
                                            function_variables.set(
                                                attr_name, "".join(attr_value_list)
                                            )
                                elif (
                                    attr_name.lower()
                                    == self.SET_CONTEXT_VARIABLE_TAG.lower()
                                ):
                                    variable_target_name = attr_value
                                elif (
                                    attr_name.lower()
                                    == self.APPEND_TO_RESULT_TAG.lower()
                                ):
                                    append_to_result_name = attr_value
                                else:
                                    function_variables.set(attr_name, attr_value)

                        keys_to_ignore = list(function_variables._variables.keys())
                        result = await self.kernel.run_on_vars_async(
                            function_variables, skill_function
                        )

                        for key in function_variables._variables.keys():
                            if (
                                key.lower() not in keys_to_ignore
                                and function_variables.get(key)
                            ):
                                context.variables.set(key, function_variables.get(key))

                        context.variables.update(str(result.variables))

                        if variable_target_name:
                            context.variables.set(variable_target_name, result.result)

                        if append_to_result_name:
                            _, results_so_far = context.variables.get(Plan.RESULT_KEY)
                            context.variables.set(
                                Plan.RESULT_KEY,
                                "{}\n\n{}\n{}".format(
                                    results_so_far, append_to_result_name, result.result
                                ).strip(),
                            )

                        process_functions = False
                    else:
                        context.log.info(
                            "{0}: appending function node {1}".format(
                                parent_node_name, skill_function_name
                            )
                        )
                        step_and_text_results.append(
                            "{0}{1}".format(indent, ET.tostring(o2, encoding="unicode"))
                        )
                    continue

                step_and_text_results.append(
                    "{0}{1}".format(indent, ET.tostring(o2, encoding="unicode"))
                )

        return "\n".join(step_and_text_results).replace("\r\n", "\n")

    def gather_goal(self, xml_doc: ET.ElementTree) -> Tuple[str, str]:
        goal_node = xml_doc.findall(".//{}".format(self.GOAL_TAG))
        if not goal_node:
            raise PlanningException(PlanningErrorCode.INVALID_PLAN, "No goal found.")
        goal_txt = goal_node[0].text.strip() if goal_node[0].text else ""
        goal_content = "<{0}>{1}</{0}>".format(
            self.GOAL_TAG, goal_txt.replace("\r\n", "\n").strip()
        )
        return (goal_txt, goal_content)

    def get_skill_function_names(self, skill_function_name):
        skill_name, function_name = (
            skill_function_name.split(".")
            if "." in skill_function_name
            else (skill_function_name, "")
        )
        return (skill_name, function_name)
