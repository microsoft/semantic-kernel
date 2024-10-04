# Copyright (c) Microsoft. All rights reserved.

import asyncio
import json
import logging
import os
import re
import sys
from typing import TYPE_CHECKING, Dict, List, Optional

if sys.version_info >= (3, 9):
    from typing import Annotated
else:
    from typing_extensions import Annotated

from semantic_kernel.exceptions import PlannerCreatePlanError, PlannerExecutionException, PlannerInvalidPlanError
from semantic_kernel.functions.function_result import FunctionResult
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata
from semantic_kernel.functions.kernel_parameter_metadata import KernelParameterMetadata
from semantic_kernel.kernel import Kernel
from semantic_kernel.planners.plan import Plan
from semantic_kernel.planners.planning_exception import PlanningException
from semantic_kernel.planners.stepwise_planner.stepwise_planner_config import (
    StepwisePlannerConfig,
)
from semantic_kernel.planners.stepwise_planner.system_step import SystemStep
from semantic_kernel.prompt_template.prompt_template_config import (
    PromptTemplateConfig,
)
from semantic_kernel.planners.stepwise_planner.stepwise_planner_config import StepwisePlannerConfig
from semantic_kernel.planners.stepwise_planner.system_step import SystemStep
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig

if TYPE_CHECKING:
    from semantic_kernel.functions.kernel_function import KernelFunction

logger: logging.Logger = logging.getLogger(__name__)

CUR_DIR = os.path.dirname(os.path.realpath(__file__))
PROMPT_CONFIG_FILE_PATH = os.path.join(CUR_DIR, "Plugins/StepwiseStep/config.json")
PROMPT_TEMPLATE_FILE_PATH = os.path.join(CUR_DIR, "Plugins/StepwiseStep/skprompt.txt")


def read_file(file_path: str) -> str:
    with open(file_path, "r") as file:
        return file.read()


# TODO: Original C# uses "StepwisePlanner_Excluded" for RESTRICTED_PLUGIN_NAME
RESTRICTED_PLUGIN_NAME = "StepwisePlanner"
S_FINAL_ANSWER_REGEX = re.compile(r"\[FINAL[_\s\-]ANSWER\](?P<final_answer>.+)", re.DOTALL)
S_THOUGHT_REGEX = re.compile(r"(\[THOUGHT\])?(?P<thought>.+?)(?=\[ACTION\]|$)", re.DOTALL)
S_ACTION_REGEX = re.compile(r"\[ACTION\][^{}]*({(?:[^{}]*{[^{}]*})*[^{}]*})", re.DOTALL)

ACTION = "[ACTION]"
THOUGHT = "[THOUGHT]"
OBSERVATION = "[OBSERVATION]"
SCRATCH_PAD_PREFIX = (
    "This was my previous work (but they haven't seen any of it!" " They only see what I return as final answer):"
)


def is_null_or_empty(value: Optional[str] = None) -> bool:
    return value is None or value == ""


class StepwisePlanner:
    config: StepwisePlannerConfig
    _arguments: "KernelArguments"
    _function_flow_function: "KernelFunction"

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
        self.config.excluded_plugins.append(RESTRICTED_PLUGIN_NAME)

        prompt_config = prompt_user_config or PromptTemplateConfig()
        prompt_template = prompt or read_file(PROMPT_TEMPLATE_FILE_PATH)

        if prompt_user_config is None:
            prompt_config = PromptTemplateConfig.from_json(read_file(PROMPT_CONFIG_FILE_PATH))

        for service in prompt_config.execution_settings.values():
            service.extension_data["max_tokens"] = self.config.max_tokens
        prompt_config.template = prompt_template

        self._system_step_function = self.import_function_from_prompt(kernel, "StepwiseStep", prompt_config)
        self._native_functions = self._kernel.import_plugin(self, RESTRICTED_PLUGIN_NAME)
        self._native_functions = self._kernel.import_plugin_from_object(self, RESTRICTED_PLUGIN_NAME)

        self._context = KernelArguments()

    @property
    def metadata(self) -> KernelFunctionMetadata:
        return KernelFunctionMetadata(
            name="StepwisePlanner",
            plugin_name="planners",
            description="",
            parameters=[
                KernelParameterMetadata(name="goal", description="The goal to achieve", default_value="", required=True)
                KernelParameterMetadata(
                    name="goal", description="The goal to achieve", default_value="", is_required=True
                )
            ],
            is_prompt=True,
            is_asynchronous=True,
        )

    def create_plan(self, goal: str) -> Plan:
        if is_null_or_empty(goal):
            raise PlanningException(PlanningException.ErrorCodes.InvalidGoal, "The goal specified is empty")
            raise PlannerInvalidPlanError("The goal specified is empty")

        function_descriptions = self.get_function_descriptions()

        plan_step: Plan = Plan.from_function(self._native_functions["ExecutePlan"])
        plan_step.parameters["function_descriptions"] = function_descriptions
        plan_step.parameters["question"] = goal

        plan_step._outputs.append("agent_scratch_pad")
        plan_step._outputs.append("step_count")
        plan_step._outputs.append("plugin_count")
        plan_step._outputs.append("steps_taken")

        plan = Plan(goal)
        plan = Plan(description=goal)

        plan.add_steps([plan_step])

        return plan

    # TODO: sync C# with https://github.com/microsoft/semantic-kernel/pull/1195
    @kernel_function(name="ExecutePlan", description="Execute a plan")
    async def execute_plan(
        self,
        question: Annotated[str, "The question to answer"],
        function_descriptions: Annotated[List[str], "List of tool descriptions"],
    ) -> FunctionResult:
        steps_taken: List[SystemStep] = []
        if not is_null_or_empty(question):
            for i in range(self.config.max_iterations):
                scratch_pad = self.create_scratch_pad(question, steps_taken)

                self._arguments["agent_scratch_pad"] = scratch_pad

                llm_response = await self._system_step_function.invoke(self._kernel, self._arguments)

                if isinstance(llm_response, FunctionResult) and "error" in llm_response.metadata:
                    raise PlanningException(
                        PlanningException.ErrorCodes.UnknownError,
                        f"Error occurred while executing stepwise plan: {llm_response.metadata['error']}",
                        llm_response.metadata["error"],
                    )
                    raise PlannerExecutionException(
                        f"Error occurred while executing stepwise plan: {llm_response.metadata['error']}",
                    ) from llm_response.metadata["error"]

                action_text = str(llm_response).strip()
                logger.debug(f"Response: {action_text}")

                next_step = self.parse_result(action_text)
                steps_taken.append(next_step)

                if not is_null_or_empty(next_step.final_answer):
                    logger.debug(f"Final Answer: {next_step.final_answer}")

                    self._arguments["input"] = next_step.final_answer
                    updated_scratch_pad = self.create_scratch_pad(question, steps_taken)
                    self._arguments["agent_scratch_pad"] = updated_scratch_pad

                    # Add additional results to the context
                    self.add_execution_stats_to_arguments(steps_taken, self._arguments)

                    return FunctionResult(
                        function=self.metadata,
                        value=next_step.final_answer,
                        metadata={"arguments": self._arguments},
                    )

                logger.debug(f"Thoughts: {next_step.thought}")

                if not is_null_or_empty(next_step.action):
                    logger.info(f"Action: {next_step.action}. Iteration: {i+1}.")
                    logger.debug(
                        f"Action: {next_step.action}({next_step.action_variables}). Iteration: {i+1}.",
                    )

                    try:
                        await asyncio.sleep(self.config.min_iteration_time_ms / 1000)
                        result = await self.invoke_action(next_step.action, next_step.action_variables)

                        if is_null_or_empty(result):
                            next_step.observation = "Got no result from action"
                        else:
                            next_step.observation = result

                    except Exception as e:
                        next_step.observation = f"Error invoking action {next_step.action}: {str(e)}"
                        logger.warning(f"Error invoking action {next_step.action}")

                    logger.debug(f"Observation: {next_step.observation}")
                else:
                    logger.info("Action: No action to take")

                # sleep 3 seconds
                await asyncio.sleep(self.config.min_iteration_time_ms / 1000)

            steps_taken_str = json.dumps([s.__dict__ for s in steps_taken], indent=4)
            self._arguments["input"] = f"Result not found, review _steps_taken to see what happened.\n{steps_taken_str}"
        else:
            self._arguments["input"] = "Question not found."

        return FunctionResult(
            function=self.metadata,
            value=self._arguments["input"],
            metadata={"arguments": self._arguments},
        )

    def parse_result(self, input: str) -> SystemStep:
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
        elif ACTION not in input:
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
                    result.observation = f"System step parsing error, empty JSON: {action_json}"
                else:
                    result.action = system_step_results["action"]
                    result.action_variables = system_step_results["action_variables"]
            except Exception:
                result.observation = f"System step parsing error, invalid JSON: {action_json}"

        if is_null_or_empty(result.thought) and is_null_or_empty(result.action):
            result.observation = (
                "System step error, no thought or action found.",
                "Please give a valid thought and/or action.",
            )

        return result

    def add_execution_stats_to_arguments(self, steps_taken: List[SystemStep], arguments: KernelArguments):
        arguments["step_count"] = str(len(steps_taken))
        arguments["steps_taken"] = json.dumps([s.__dict__ for s in steps_taken], indent=4)

        action_counts: Dict[str, int] = {}
        for step in steps_taken:
            if is_null_or_empty(step.action):
                continue

            current_count = action_counts.get(step.action, 0)
            action_counts[step.action] = current_count + 1

        plugin_call_list_with_counts = [f"{plugin}({action_counts[plugin]})" for plugin in action_counts]
        plugin_call_list_with_counts = ", ".join(plugin_call_list_with_counts)
        plugin_call_count_str = str(sum(action_counts.values()))

        arguments["plugin_count"] = f"{plugin_call_count_str} ({plugin_call_list_with_counts})"

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
                logger.debug(f"Scratchpad is too long, truncating. Skipping {i + 1} steps.")
                break

            s = steps_taken[i]

            if not is_null_or_empty(s.observation):
                scratch_pad_lines.insert(insert_point, f"{OBSERVATION}\n{s.observation}")

            if not is_null_or_empty(s.action):
                scratch_pad_lines.insert(
                    insert_point,
                    f'{ACTION}\n{{"action": "{s.action}", "action_variables": {json.dumps(s.action_variables)}}}',
                )

            if i != 0:
                scratch_pad_lines.insert(insert_point, f"{THOUGHT}\n{s.thought}")

        scratch_pad = "\n".join(scratch_pad_lines).strip()

        if not (is_null_or_empty(scratch_pad.strip())):
            logger.debug(f"Scratchpad: {scratch_pad}")

        return scratch_pad

    async def invoke_action(self, action_name: str, action_variables: Dict[str, str]) -> str:
        available_functions = self.get_available_functions()
        target_function = next(
            (f for f in available_functions if self.to_fully_qualified_name(f) == action_name),
            None,
        )

        if target_function is None:
            raise PlanningException(
                PlanningException.ErrorCodes.UnknownError,
                f"The function '{action_name}' was not found.",
            )
            raise PlannerExecutionException(f"The function '{action_name}' was not found.")

        try:
            function = self._kernel.func(target_function.plugin_name, target_function.name)
            action_arguments = self.create_action_arguments(action_variables)

            result = await function.invoke(self._kernel, action_arguments)

            if isinstance(result, FunctionResult) and "error" in result.metadata:
                logger.error(f"Error occurred: {result.metadata['error']}")
                return f"Error occurred: {result.metadata['error']}"

            logger.debug(f"Invoked {target_function.name}. Result: {result}")

            return str(result)

        except Exception as e:
            error_msg = (
                f"Something went wrong in system step: {target_function.plugin_name}.{target_function.name}. Error: {e}"
            )
            logger.error(error_msg)
            return error_msg

    def create_action_arguments(self, action_variables: Dict[str, str]) -> KernelArguments:
        action_arguments = KernelArguments()
        if action_variables is not None:
            for k, v in action_variables.items():
                action_arguments[k] = v

        return action_arguments

    def get_available_functions(self) -> List[KernelFunctionMetadata]:
        if self._kernel.plugins is None:
            raise PlanningException(
                PlanningException.ErrorCodes.CreatePlanError,
                "Plugin collection not found in the kernel",
            )
            raise PlannerCreatePlanError("Plugin collection not found in the kernel")

        excluded_plugins = self.config.excluded_plugins or []
        excluded_functions = self.config.excluded_functions or []
        available_functions = [
            func
            for func in self._kernel.plugins.get_list_of_function_metadata()
            if (func.plugin_name not in excluded_plugins and func.name not in excluded_functions)
        ]
        available_functions = sorted(available_functions, key=lambda x: (x.plugin_name, x.name))

        return available_functions

    def get_function_descriptions(self) -> str:
        available_functions = self.get_available_functions()

        function_descriptions = "\n".join([self.to_manual_string(f) for f in available_functions])
        return function_descriptions

    def import_function_from_prompt(
        self,
        kernel: Kernel,
        function_name: str,
        config: PromptTemplateConfig = None,
    ) -> "KernelFunction":
        return kernel.create_function_from_prompt(
            plugin_name=RESTRICTED_PLUGIN_NAME, function_name=function_name, prompt_template_config=config
        )

    def to_manual_string(self, function: KernelFunctionMetadata) -> str:
        inputs = [
            f"    - {parameter.name}: {parameter.description}"
            + (f" (default value={parameter.default_value})" if parameter.default_value else "")
            for parameter in function.parameters
        ]
        inputs = "\n".join(inputs)

        function_description = function.description.strip()

        if is_null_or_empty(inputs):
            return f"{self.to_fully_qualified_name(function)}: {function_description}\n  inputs: None\n"

        return f"{self.to_fully_qualified_name(function)}: {function_description}\n  inputs:\n{inputs}\n"

    def to_fully_qualified_name(self, function: KernelFunctionMetadata):
        return f"{function.plugin_name}.{function.name}"
