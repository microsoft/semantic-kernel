from logging import Logger
from typing import Optional

import regex
from python.semantic_kernel.orchestration.context_variables import ContextVariables

from semantic_kernel.kernel import Kernel
from semantic_kernel.orchestration.sk_context import SKContext
from semantic_kernel.orchestration.sk_function_base import SKFunctionBase
from semantic_kernel.planning.plan import Plan
from semantic_kernel.utils.null_logger import NullLogger


class ActionPlanner:
    STOP_SEQUENCE = "#END-OF-PLAN"
    PLUGIN_NAME = "self"

    _planner_function: SKFunctionBase
    _context: SKContext
    _kernel: Kernel
    _logger: Logger

    def __init__(
        self,
        kernel: Kernel,
        prompt: Optional[str] = None,
        logger: Optional[Logger] = None,
    ) -> None:
        self._logger = NullLogger() if logger is None else logger

        prompt_template = (
            prompt if prompt is not None else ActionPlanner.ACTION_PLANNER_PROMPT
        )

        self._planner_function = self._kernel.create_semantic_function(
            skill_name=ActionPlanner.PLUGIN_NAME,
            prompt_template=prompt_template,
            max_tokens=1024,
            stop_sequences=[ActionPlanner.STOP_SEQUENCE],
        )

        kernel.import_skill(self, ActionPlanner.PLUGIN_NAME)
        self._kernel = kernel
        self._context = kernel.create_new_context()

    async def create_plan(self, goal: str) -> Plan:
        if not goal or goal is None:
            # throw invalid goal planner exception
            return None

        self._context.variables.update(goal)

        result = await self._planner_function.invoke_async(context=self._context)
        # Filter out good JSON from the input in case additional text is present
        json_regex = r"\{(?:[^{}]|(?R))*\}"
        result_dict = regex.search(json_regex, result).group()

        if not result_dict or result_dict is None:
            # throw invalid plan planner exception
            return None

        variables = ContextVariables()
        for param in result_dict["plan"]["parameters"]:
            if result_dict["plan"]["parameters"][param] is not None:
                variables.set(param, result_dict["plan"]["parameters"][param])

        if "." in result_dict["plan"]["function"]:
            parts = result_dict["plan"]["function"].split(".")
            new_plan = Plan(
                description=goal,
                state=variables,
                function=self._context.skills.get_function(parts[0], parts[1]),
            )
        elif (
            not result_dict["plan"]["function"]
            or result_dict["plan"]["function"] is not None
        ):
            new_plan = Plan(
                description=goal,
                state=variables,
                function=self._context.skills.get_function(
                    result_dict["plan"]["function"]
                ),
            )
        else:
            new_plan = Plan(description=goal, state=variables)

        return new_plan

    ACTION_PLANNER_PROMPT = """A planner takes a list of functions, a goal, and chooses which function to use.
For each function the list includes details about the input parameters.
[START OF EXAMPLES]
{{this.GoodExamples}}
{{this.EdgeCaseExamples}}
[END OF EXAMPLES]
[REAL SCENARIO STARTS HERE]
- List of functions:
{{this.ListOfFunctions}}
- End list of functions.
Goal: {{ $input }}"""
