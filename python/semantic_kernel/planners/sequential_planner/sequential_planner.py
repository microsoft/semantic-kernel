# Copyright (c) Microsoft. All rights reserved.

import os

from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.const import DEFAULT_SERVICE_NAME, METADATA_EXCEPTION_KEY
from semantic_kernel.exceptions import PlannerCreatePlanError, PlannerException, PlannerInvalidGoalError
from semantic_kernel.functions.function_result import FunctionResult
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.kernel import Kernel
from semantic_kernel.planners.plan import Plan
from semantic_kernel.planners.sequential_planner.sequential_planner_config import SequentialPlannerConfig
from semantic_kernel.planners.sequential_planner.sequential_planner_extensions import SequentialPlannerKernelExtension
from semantic_kernel.planners.sequential_planner.sequential_planner_parser import SequentialPlanParser
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig

SEQUENTIAL_PLANNER_DEFAULT_DESCRIPTION = (
    "Given a request or command or goal generate a step by step plan to "
    "fulfill the request using functions. This ability is also known as decision making and function flow"
)

CUR_DIR = os.path.dirname(os.path.realpath(__file__))
PROMPT_CONFIG_FILE_PATH = os.path.join(CUR_DIR, "Plugins/SequentialPlanning/config.json")
PROMPT_TEMPLATE_FILE_PATH = os.path.join(CUR_DIR, "Plugins/SequentialPlanning/skprompt.txt")


def read_file(file_path: str) -> str:
    """Reads the content of a file."""
    with open(file_path) as file:
        return file.read()


class SequentialPlanner:
    """Sequential planner class."""

    RESTRICTED_PLUGIN_NAME = "SequentialPlanner_Excluded"

    config: SequentialPlannerConfig
    _kernel: "Kernel"
    _arguments: "KernelArguments"
    _function_flow_function: "KernelFunction"

    def __init__(
        self,
        kernel: Kernel,
        service_id: str,
        config: SequentialPlannerConfig = None,
        prompt: str | None = None,
    ) -> None:
        """Initializes a new instance of the SequentialPlanner class.

        Args:
            kernel (Kernel): The kernel instance to use for planning
            service_id (str): The service id to use to get the AI service
            config (SequentialPlannerConfig, optional): The configuration to use for planning. Defaults to None.
            prompt (str, optional): The prompt to use for planning. Defaults to None.
        """
        self.config = config or SequentialPlannerConfig()

        self.config.excluded_plugins.append(self.RESTRICTED_PLUGIN_NAME)

        self._kernel = kernel
        self._arguments = KernelArguments()
        self._function_flow_function = self._init_flow_function(prompt, service_id)

    def _init_flow_function(self, prompt: str, service_id: str) -> "KernelFunction":
        prompt_config = PromptTemplateConfig.from_json(read_file(PROMPT_CONFIG_FILE_PATH))
        prompt_template = prompt or read_file(PROMPT_TEMPLATE_FILE_PATH)
        if service_id in prompt_config.execution_settings:
            prompt_config.execution_settings[service_id].extension_data["max_tokens"] = self.config.max_tokens
        elif DEFAULT_SERVICE_NAME in prompt_config.execution_settings:
            prompt_config.execution_settings[DEFAULT_SERVICE_NAME].extension_data["max_tokens"] = self.config.max_tokens
        else:
            prompt_config.execution_settings[service_id] = PromptExecutionSettings(
                service_id=service_id, max_tokens=self.config.max_tokens
            )
        prompt_config.template = prompt_template

        # if a service_id is provided, use it instead of the default
        if (
            service_id
            and service_id not in prompt_config.execution_settings
            and DEFAULT_SERVICE_NAME in prompt_config.execution_settings
        ):
            settings = prompt_config.execution_settings.pop(DEFAULT_SERVICE_NAME)
            prompt_config.execution_settings[service_id] = settings

        return self._kernel.add_function(
            plugin_name=self.RESTRICTED_PLUGIN_NAME,
            function_name=self.RESTRICTED_PLUGIN_NAME,
            prompt_template_config=prompt_config,
        )

    async def create_plan(self, goal: str) -> Plan:
        """Create a plan for the specified goal."""
        if len(goal) == 0:
            raise PlannerInvalidGoalError("The goal specified is empty")

        relevant_function_manual = await SequentialPlannerKernelExtension.get_functions_manual(
            self._kernel, self._arguments, goal, self.config
        )
        self._arguments["available_functions"] = relevant_function_manual
        self._arguments["input"] = goal

        plan_result = await self._function_flow_function.invoke(self._kernel, self._arguments)

        if isinstance(plan_result, FunctionResult) and METADATA_EXCEPTION_KEY in plan_result.metadata:
            raise PlannerCreatePlanError(
                f"Error creating plan for goal: {plan_result.metadata['exception']}",
            ) from plan_result.metadata[METADATA_EXCEPTION_KEY]

        plan_result_string = str(plan_result).strip()

        try:
            plan = SequentialPlanParser.to_plan_from_xml(
                xml_string=plan_result_string,
                goal=goal,
                kernel=self._kernel,
                get_plugin_function=self.config.get_plugin_function,
                allow_missing_functions=self.config.allow_missing_functions,
            )

            if len(plan._steps) == 0:
                raise PlannerCreatePlanError(
                    "Not possible to create plan for goal with available functions.\n",
                    f"Goal:{goal}\nFunctions:\n{relevant_function_manual}",
                )

            return plan

        except PlannerException as e:
            raise e
        except Exception as e:
            raise PlannerException(
                "Unknown error creating plan",
                e,
            ) from e
