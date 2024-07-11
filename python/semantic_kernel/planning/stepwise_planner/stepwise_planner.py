# Copyright (c) Microsoft. All rights reserved.

import asyncio
import itertools
import json
import os
import re
from typing import TYPE_CHECKING, Dict, List

from semantic_kernel.kernel import Kernel
from semantic_kernel.orchestration.sk_context import SKContext
from semantic_kernel.planning.plan import Plan
from semantic_kernel.planning.planning_exception import PlanningException
from semantic_kernel.planning.stepwise_planner.stepwise_planner_config import (
    StepwisePlannerConfig,
)
from semantic_kernel.planning.stepwise_planner.system_step import SystemStep
from semantic_kernel.semantic_functions.prompt_template import PromptTemplate
from semantic_kernel.semantic_functions.prompt_template_config import (
    PromptTemplateConfig,
)
from semantic_kernel.semantic_functions.semantic_function_config import (
    SemanticFunctionConfig,
)
from semantic_kernel.skill_definition.function_view import FunctionView
from semantic_kernel.skill_definition.sk_function_context_parameter_decorator import (
    sk_function_context_parameter,
)
from semantic_kernel.skill_definition.sk_function_decorator import sk_function

if TYPE_CHECKING:
    from semantic_kernel.orchestration.sk_function_base import SKFunctionBase


CUR_DIR = os.path.dirname(os.path.realpath(__file__))
PROMPT_CONFIG_FILE_PATH = os.path.join(CUR_DIR, "Skills/StepwiseStep/config.json")
PROMPT_TEMPLATE_FILE_PATH = os.path.join(CUR_DIR, "Skills/StepwiseStep/skprompt.txt")


def read_file(file_path: str) -> str:
    with open(file_path, "r") as file:
        return file.read()


# TODO: Original C# uses "StepwisePlanner_Excluded" for RESTRICTED_SKILL_NAME
RESTRICTED_SKILL_NAME = "StepwisePlanner"
S_FINAL_ANSWER_REGEX = re.compile(
    r"\[FINAL[_\s\-]ANSWER\](?P<final_answer>.+)", re.DOTALL
)
S_THOUGHT_REGEX = re.compile(
    r"(\[THOUGHT\])?(?P<thought>.+?)(?=\[ACTION\]|$)", re.DOTALL
)
S_ACTION_REGEX = re.compile(r"\[ACTION\][^{}]*({(?:[^{}]*{[^{}]*})*[^{}]*})", re.DOTALL)

ACTION = "[ACTION]"
THOUGHT = "[THOUGHT]"
OBSERVATION = "[OBSERVATION]"
SCRATCH_PAD_PREFIX = (
    "This was my previous work (but they haven't seen any of it!"
    " They only see what I return as final answer):"
)


def is_null_or_empty(value: str) -> bool:
    return value is None or value == ""


class StepwisePlanner:
    config: StepwisePlannerConfig
    _context: "SKContext"
    _function_flow_function: "SKFunctionBase"

    def __init__(
        self,
        kernel: Kernel,
        config: StepwisePlannerConfig = None,
        prompt: str = None,
        prompt_user_config: PromptTemplateConfig = None,
    ):
        assert isinstance(kernel, Kernel)
        self._kernel = kernel

        self.config = config or StepwisePlannerConfig()
        self.config.excluded_skills.append(RESTRICTED_SKILL_NAME)

        prompt_config = prompt_user_config or PromptTemplateConfig()
        prompt_template = prompt or read_file(PROMPT_TEMPLATE_FILE_PATH)

        if prompt_user_config is None:
            prompt_config = PromptTemplateConfig.from_json(
                read_file(PROMPT_CONFIG_FILE_PATH)
            )

        prompt_config.completion.max_tokens = self.config.max_tokens

        self._system_step_function = self.import_semantic_function(
            kernel, "StepwiseStep", prompt_template, prompt_config
        )
        self._native_functions = self._kernel.import_skill(self, RESTRICTED_SKILL_NAME)

        self._context = kernel.create_new_context()
        self._logger = self._kernel.logger

    def create_plan(self, goal: str) -> Plan:
        if is_null_or_empty(goal):
            raise PlanningException(
                PlanningException.ErrorCodes.InvalidGoal, "The goal specified is empty"
            )

        function_descriptions = self.get_function_descriptions()

        plan_step: Plan = Plan.from_function(self._native_functions["ExecutePlan"])
        plan_step.parameters.set("function_descriptions", function_descriptions)
        plan_step.parameters.set("question", goal)

        plan_step._outputs.append("agent_scratch_pad")
        plan_step._outputs.append("step_count")
        plan_step._outputs.append("skill_count")
        plan_step._outputs.append("steps_taken")

        plan = Plan(goal)

        plan.add_steps([plan_step])

        return plan

    # TODO: sync C# with https://github.com/microsoft/semantic-kernel/pull/1195
    @sk_function(name="ExecutePlan", description="Execute a plan")
    @sk_function_context_parameter(
        name="question", description="The question to answer"
    )
    @sk_function_context_parameter(
        name="function_descriptions", description="List of tool descriptions"
    )
    async def execute_plan_async(self, context: SKContext):
        question = context["question"]

        steps_taken: List[SystemStep] = []
        if not is_null_or_empty(question):
            for i in range(self.config.max_iterations):
                scratch_pad = self.create_scratch_pad(question, steps_taken)

                context.variables.set("agent_scratch_pad", scratch_pad)

                llm_response = await self._system_step_function.invoke_async(
                    context=context
                )

                if llm_response.error_occurred:
                    raise PlanningException(
                        PlanningException.ErrorCodes.UnknownError,
                        f"Error occurred while executing stepwise plan: {llm_response.last_exception}",
                        llm_response.last_exception,
                    )

                action_text = llm_response.result.strip()
                self._logger.debug(f"Response: {action_text}")

                next_step = self.parse_result(action_text)
                steps_taken.append(next_step)

                if not is_null_or_empty(next_step.final_answer):
                    self._logger.debug(f"Final Answer: {next_step.final_answer}")

                    context.variables.update(next_step.final_answer)
                    updated_scratch_pad = self.create_scratch_pad(question, steps_taken)
                    context.variables.set("agent_scratch_pad", updated_scratch_pad)

                    # Add additional results to the context
                    self.add_execution_stats_to_context(steps_taken, context)

                    return context

                self._logger.debug("Thoughts: {next_step.thought}")

                if not is_null_or_empty(next_step.action):
                    self._logger.info(f"Action: {next_step.action}. Iteration: {i+1}.")
                    self._logger.debug(
                        f"Action: {next_step.action}({next_step.action_variables}). Iteration: {i+1}.",
                    )

                    try:
                        await asyncio.sleep(self.config.min_iteration_time_ms / 1000)
                        result = await self.invoke_action_async(
                            next_step.action, next_step.action_variables
                        )

                        if is_null_or_empty(result):
                            next_step.observation = "Got no result from action"
                        else:
                            next_step.observation = result

                    except Exception as e:
                        next_step.observation = (
                            f"Error invoking action {next_step.action}: {str(e)}"
                        )
                        self._logger.warning(
                            f"Error invoking action {next_step.action}"
                        )

                    self._logger.debug(f"Observation: {next_step.observation}")
                else:
                    self._logger.info("Action: No action to take")

                # sleep 3 seconds
                await asyncio.sleep(self.config.min_iteration_time_ms / 1000)

            steps_taken_str = json.dumps([s.__dict__ for s in steps_taken], indent=4)
            context.variables.update(
                f"Result not found, review _steps_taken to see what happened.\n{steps_taken_str}"
            )
        else:
            context.variables.update("Question not found.")

        return context

    def parse_result(self, input: str):
        result = SystemStep(original_response=input)

        # Extract final answer
        final_answer_match = re.search(S_FINAL_ANSWER_REGEX, input)

        if final_answer_match:
            result.final_answer = final_answer_match.group(1).strip()
            return result

        # Extract thought
        thought_match = re.search(S_THOUGHT_REGEX, input)

        if thought_match:
            result.thought = thought_match.group(0).strip()
        elif not input.contains(ACTION):
            result.thought = input
        else:
            raise ValueError("Unexpected input format")

        result.thought = result.thought.replace(THOUGHT, "").strip()

        # Extract action
        action_match = re.search(S_ACTION_REGEX, input)

        if action_match:
            action_json = action_match.group(1).strip()

            try:
                system_step_results = json.loads(action_json)

                if system_step_results is None or len(system_step_results) == 0:
                    result.observation = (
                        f"System step parsing error, empty JSON: {action_json}"
                    )
                else:
                    result.action = system_step_results["action"]
                    result.action_variables = system_step_results["action_variables"]
            except Exception:
                result.observation = (
                    f"System step parsing error, invalid JSON: {action_json}"
                )

        if is_null_or_empty(result.thought) and is_null_or_empty(result.action):
            result.observation = (
                "System step error, no thought or action found.",
                "Please give a valid thought and/or action.",
            )

        return result

    def add_execution_stats_to_context(
        self, steps_taken: List[SystemStep], context: SKContext
    ):
        context.variables.set("step_count", str(len(steps_taken)))
        context.variables.set(
            "steps_taken", json.dumps([s.__dict__ for s in steps_taken], indent=4)
        )

        action_counts: Dict[str, int] = {}
        for step in steps_taken:
            if is_null_or_empty(step.action):
                continue

            current_count = action_counts.get(step.action, 0)
            action_counts[step.action] = current_count + 1

        skill_call_list_with_counts = [
            f"{skill}({action_counts[skill]})" for skill in action_counts
        ]
        skill_call_list_with_counts = ", ".join(skill_call_list_with_counts)
        skill_call_count_str = str(sum(action_counts.values()))

        context.variables.set(
            "skill_count", f"{skill_call_count_str} ({skill_call_list_with_counts})"
        )

    def create_scratch_pad(self, question: str, steps_taken: List[SystemStep]) -> str:
        if len(steps_taken) == 0:
            return ""

        scratch_pad_lines: List[str] = []

        # Add the original first thought
        scratch_pad_lines.append(SCRATCH_PAD_PREFIX)
        scratch_pad_lines.append(f"{THOUGHT}\n{steps_taken[0].thought}")

        # Keep track of where to insert the next step
        insert_point = len(scratch_pad_lines)

        for i in reversed(range(len(steps_taken))):
            if len(scratch_pad_lines) / 4.0 > (self.config.max_tokens * 0.75):
                self._logger.debug(
                    f"Scratchpad is too long, truncating. Skipping {i + 1} steps."
                )
                break

            s = steps_taken[i]

            if not is_null_or_empty(s.observation):
                scratch_pad_lines.insert(
                    insert_point, f"{OBSERVATION}\n{s.observation}"
                )

            if not is_null_or_empty(s.action):
                scratch_pad_lines.insert(
                    insert_point,
                    f'{ACTION}\n{{"action": "{s.action}", "action_variables": {json.dumps(s.action_variables)}}}',
                )

            if i != 0:
                scratch_pad_lines.insert(insert_point, f"{THOUGHT}\n{s.thought}")

        scratch_pad = "\n".join(scratch_pad_lines).strip()

        if not (is_null_or_empty(scratch_pad.strip())):
            self._logger.debug(f"Scratchpad: {scratch_pad}")

        return scratch_pad

    async def invoke_action_async(
        self, action_name: str, action_variables: Dict[str, str]
    ) -> str:
        available_functions = self.get_available_functions()
        target_function = next(
            (
                f
                for f in available_functions
                if self.to_fully_qualified_name(f) == action_name
            ),
            None,
        )

        if target_function is None:
            raise PlanningException(
                PlanningException.ErrorCodes.UnknownError,
                f"The function '{action_name}' was not found.",
            )

        try:
            function = self._kernel.func(
                target_function.skill_name, target_function.name
            )
            action_context = self.create_action_context(action_variables)

            result = await function.invoke_async(context=action_context)

            if result.error_occurred:
                self._logger.error(f"Error occurred: {result.last_exception}")
                return f"Error occurred: {result.last_exception}"

            self._logger.debug(
                f"Invoked {target_function.name}. Result: {result.result}"
            )

            return result.result

        except Exception as e:
            self._logger.error(
                e,
                f"Something went wrong in system step: {target_function.skill_name}.{target_function.name}. Error: {e}",
            )
            return (
                "Something went wrong in system step: ",
                f"{target_function.skill_name}.{target_function.name}. Error: {e}",
            )

    def create_action_context(self, action_variables: Dict[str, str]) -> SKContext:
        action_context = self._kernel.create_new_context()
        if action_variables is not None:
            for k, v in action_variables.items():
                action_context.variables.set(k, v)

        return action_context

    def get_available_functions(self) -> List[FunctionView]:
        functions_view = self._context.skills.get_functions_view()

        excluded_skills = self.config.excluded_skills or []
        excluded_functions = self.config.excluded_functions or []

        available_functions: List[FunctionView] = [
            *functions_view.semantic_functions.values(),
            *functions_view.native_functions.values(),
        ]
        available_functions = itertools.chain.from_iterable(available_functions)
        available_functions = [
            func
            for func in available_functions
            if (
                func.skill_name not in excluded_skills
                and func.name not in excluded_functions
            )
        ]
        available_functions = sorted(
            available_functions, key=lambda x: (x.skill_name, x.name)
        )

        return available_functions

    def get_function_descriptions(self) -> str:
        available_functions = self.get_available_functions()

        function_descriptions = "\n".join(
            [self.to_manual_string(f) for f in available_functions]
        )
        return function_descriptions

    def import_semantic_function(
        self,
        kernel: Kernel,
        function_name: str,
        prompt_template: str,
        config: PromptTemplateConfig = None,
    ) -> "SKFunctionBase":
        template = PromptTemplate(
            prompt_template, kernel.prompt_template_engine, config
        )
        function_config = SemanticFunctionConfig(config, template)

        return kernel.register_semantic_function(
            RESTRICTED_SKILL_NAME, function_name, function_config
        )

    def to_manual_string(self, function: FunctionView) -> str:
        inputs = [
            f"    - {parameter.name}: {parameter.description}"
            + (
                f" (default value={parameter.default_value})"
                if parameter.default_value
                else ""
            )
            for parameter in function.parameters
        ]
        inputs = "\n".join(inputs)

        function_description = function.description.strip()

        if is_null_or_empty(inputs):
            return f"{self.to_fully_qualified_name(function)}: {function_description}\n  inputs: None\n"

        return f"{self.to_fully_qualified_name(function)}: {function_description}\n  inputs:\n{inputs}\n"

    def to_fully_qualified_name(self, function: FunctionView):
        return f"{function.skill_name}.{function.name}"
