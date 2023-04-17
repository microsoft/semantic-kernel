# Copyright (c) Microsoft. All rights reserved.
import logging
import xml.etree.ElementTree as ET

from semantic_kernel.kernel_base import KernelBase
from semantic_kernel.orchestration.sk_context import SKContext
from semantic_kernel.orchestration.sk_function import SKFunction
from semantic_kernel.planning.planning_exception import (
    PlanningErrorCode,
    PlanningException,
)


class PlanRunner:
    # The tag name used in the plan xml for the user's goal/ask.
    GOAL_TAG = "goal"
    # The tag name used in the plan xml for the solution.
    SOLUTION_TAG = "solution"
    # The tag name used in the plan xml for a generic step.
    STEP_TAG = "step"
    # The tag name used in the plan xml for the context variables.
    VARIABLES_TAG = "variables"
    # Constants
    INDENT = "  "

    def __init__(self, kernel: KernelBase):
        self._kernel = kernel

    async def execute_xml_plan_async(
        self, context: SKContext, plan_payload: str, default_step_executor: SKFunction
    ):
        try:
            xml_doc = ET.fromstring(f"<xml>{plan_payload}</xml>")

            # Get the Goal
            goal_node, goal_xml_string = self._gather_goal(xml_doc, self.GOAL_TAG)

            # Get the ContextVariables and Solution
            variables = xml_doc.findall(self.VARIABLES_TAG)
            solution = xml_doc.findall(self.SOLUTION_TAG)

            # Prepare content for the new plan xml
            variables_content = []
            solution_content = []
            variables_content.append(f"<{self.VARIABLES_TAG}>")
            solution_content.append(f"<{self.SOLUTION_TAG}>")

            # Process ContextVariables nodes
            logging.debug("Processing context variables")
            # Process the context variables nodes
            step_results = self._process_node_list(variables, context)
            # Add the context variables to the new plan xml
            variables_content.append(step_results)
            variables_content.append(f"</{self.VARIABLES_TAG}>")

            # Process Solution nodes
            logging.debug("Processing solution")
            # Process the solution nodes
            step_results = self._process_node_list(solution, context)
            # Add the solution and context variables updates to the new plan xml
            solution_content.append(step_results)
            solution_content.append(f"</{self.SOLUTION_TAG}>")

            # Update the plan xml
            updated_plan = (
                goal_xml_string + "".join(variables_content) + "".join(solution_content)
            )
            updated_plan = updated_plan.strip()
            context.variables.update(updated_plan)

            # Otherwise, execute the next step in the plan
            next_plan = str(
                await self._kernel.run_async(context.variables, default_step_executor)
            ).strip()

            # And return the updated context with the updated plan xml
            context.variables.update(next_plan)
            return context
        except Exception as e:
            logging.error(f"Plan execution failed: {e}")
            raise

    def _gather_goal(self, xml_doc, GOAL_TAG):
        goal_node = xml_doc.find(GOAL_TAG)
        if goal_node is None:
            raise PlanningException(
                PlanningErrorCode.INVALID_PLAN,
                "Missing goal node in plan xml.",
            )
        return goal_node, ET.tostring(goal_node, encoding="unicode")

    def _process_node_list(self, node_list, context: SKContext):
        step_and_text_results = []
        if node_list is not None:
            for node in node_list:
                if node is None:
                    continue

                parent_node_name = node.tag
                logging.debug(f"{parent_node_name}: found node")
                for child_node in node:
                    if child_node.tag == "#text":
                        logging.debug(f"{parent_node_name}: appending text node")
                        step_and_text_results.append(child_node.text.strip())
                        continue

                    if child_node.tag == self.STEP_TAG:
                        logging.debug(
                            f"{parent_node_name}: appending step node {child_node}"
                        )
                        step_and_text_results.append(
                            f"{self.INDENT}{ET.tostring(child_node, encoding='unicode').strip()}"
                        )
                        continue

                    step_and_text_results.append(
                        f"{self.INDENT}{ET.tostring(child_node, encoding='unicode').strip()}"
                    )
        return "\n".join(step_and_text_results)
