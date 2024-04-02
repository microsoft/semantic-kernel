# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
import os
from copy import copy
from typing import Optional

import yaml

from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_prompt_execution_settings import (
    OpenAIChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion import OpenAIChatCompletion
from semantic_kernel.connectors.ai.open_ai.utils import (
    get_tool_call_object,
)
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.exceptions.planner_exceptions import PlannerInvalidConfigurationError
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.kernel import Kernel
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.planners.function_calling_stepwise_planner.function_calling_stepwise_planner_options import (
    FunctionCallingStepwisePlannerOptions,
)
from semantic_kernel.planners.function_calling_stepwise_planner.function_calling_stepwise_planner_result import (
    FunctionCallingStepwisePlannerResult,
    UserInteraction,
)
from semantic_kernel.planners.planner_extensions import PlannerKernelExtension
from semantic_kernel.prompt_template.kernel_prompt_template import KernelPromptTemplate
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig

CUR_DIR = os.path.dirname(os.path.realpath(__file__))
PLAN_YAML_FILE_PATH = os.path.join(CUR_DIR, "generate_plan.yaml")
STEP_PROMPT_FILE_PATH = os.path.join(CUR_DIR, "step_prompt.txt")

STEPWISE_PLANNER_PLUGIN_NAME = "StepwisePlanner_Excluded"

STEPWISE_USER_MESSAGE = (
    "Perform the next step of the plan if there is more work to do."
    "When you have reached a final answer, use the UserInteraction-SendFinalAnswer"
    "function to communicate this back to the user."
)

USER_INTERACTION_SEND_FINAL_ANSWER = "UserInteraction-SendFinalAnswer"

logger: logging.Logger = logging.getLogger(__name__)


class FunctionCallingStepwisePlanner(KernelBaseModel):
    service_id: str
    options: FunctionCallingStepwisePlannerOptions
    generate_plan_yaml: str
    step_prompt: str

    def __init__(self, service_id: str, options: Optional[FunctionCallingStepwisePlannerOptions] = None):
        """Initialize a new instance of the FunctionCallingStepwisePlanner

        The FunctionCallingStepwisePlanner is a planner based on top of an OpenAI Chat Completion service
        (whether it be AzureOpenAI or OpenAI), so that we can use tools.

        If the options are configured to use callbacks to get the initial plan and the step prompt,
        the planner will use those provided callbacks to get that information. Otherwise it will
        read from the default yaml plan file and the step prompt file.

        Args:
            service_id (str): The service id
            options (Optional[FunctionCallingStepwisePlannerOptions], optional): The options for
                the function calling stepwise planner. Defaults to None.
        """
        options = options or FunctionCallingStepwisePlannerOptions()
        generate_plan_yaml = (
            options.get_initial_plan() if options.get_initial_plan else open(PLAN_YAML_FILE_PATH).read()
        )
        step_prompt = options.get_step_prompt() if options.get_step_prompt else open(STEP_PROMPT_FILE_PATH).read()
        options.excluded_plugins.add(STEPWISE_PLANNER_PLUGIN_NAME)

        super().__init__(
            service_id=service_id,
            options=options,
            generate_plan_yaml=generate_plan_yaml,
            step_prompt=step_prompt,
        )

    async def invoke(
        self,
        kernel: Kernel,
        question: str,
    ) -> FunctionCallingStepwisePlannerResult:
        """
        Execute the function calling stepwise planner

        Args:
            kernel: The kernel instance
            question: The input question

        Returns:
            FunctionCallingStepwisePlannerResult: The result of the function calling stepwise planner

        Raises:
            PlannerInvalidConfigurationError: If the input question is empty
        """
        if not question:
            raise PlannerInvalidConfigurationError("Input question cannot be empty")

        try:
            chat_completion = kernel.get_service(service_id=self.service_id, type=OpenAIChatCompletion)
        except Exception as exc:
            raise PlannerInvalidConfigurationError(
                f"The OpenAI service `{self.service_id}` is not available. Please configure the AI service."
            ) from exc

        prompt_execution_settings: (
            OpenAIChatPromptExecutionSettings
        ) = self.options.execution_settings or chat_completion.get_prompt_execution_settings_class()(
            service_id=self.service_id
        )

        # Clone the kernel so that we can add planner-specific plugins without affecting the original kernel instance
        cloned_kernel = copy(kernel)
        cloned_kernel.import_plugin_from_object(UserInteraction(), "UserInteraction")

        # Create and invoke a kernel function to generate the initial plan
        initial_plan = await self._generate_plan(question, cloned_kernel)

        chat_history_for_steps = await self._build_chat_history_for_step(question, initial_plan, cloned_kernel)
        prompt_execution_settings.tool_choice = "auto"
        prompt_execution_settings.tools = get_tool_call_object(kernel, {"exclude_plugin": [self.service_id]})
        arguments = KernelArguments()
        for i in range(self.options.max_iterations):
            # sleep for a bit to avoid rate limiting
            if i > 0:
                await asyncio.sleep(self.options.min_iteration_time_ms / 1000.0)  # convert ms to sec
            # For each step, request another completion to select a function for that step
            chat_history_for_steps.add_user_message(STEPWISE_USER_MESSAGE)
            chat_result = await chat_completion.complete_chat(
                chat_history=chat_history_for_steps,
                settings=prompt_execution_settings,
                kernel=cloned_kernel,
            )
            chat_result = chat_result[0]
            chat_history_for_steps.add_message(chat_result)

            if not chat_result.tool_calls:
                chat_history_for_steps.add_user_message("That function call is invalid. Try something else!")
                continue

            # Try to get the final answer out
            if chat_result.tool_calls[0].function.name == USER_INTERACTION_SEND_FINAL_ANSWER:
                args = chat_result.tool_calls[0].function.parse_arguments()
                answer = args["answer"]
                return FunctionCallingStepwisePlannerResult(
                    final_answer=answer,
                    chat_history=chat_history_for_steps,
                    iterations=i + 1,
                )

            try:
                await chat_completion._process_tool_calls(
                    result=chat_result, kernel=cloned_kernel, chat_history=chat_history_for_steps, arguments=arguments
                )
            except Exception as exc:
                chat_history_for_steps.add_user_message(f"An error occurred during planner invocation: {exc}")
                continue

        # We're done, but the model hasn't returned a final answer.
        return FunctionCallingStepwisePlannerResult(
            final_answer="",
            chat_history=chat_history_for_steps,
            iterations=i + 1,
        )

    async def _build_chat_history_for_step(
        self,
        goal: str,
        initial_plan: str,
        kernel: Kernel,
    ) -> ChatHistory:
        """Build the chat history for the stepwise planner"""
        chat_history = ChatHistory()
        arguments = KernelArguments(
            goal=goal,
            initial_plan=initial_plan,
        )
        kernel_prompt_template = KernelPromptTemplate(
            prompt_template_config=PromptTemplateConfig(
                template=self.step_prompt,
            )
        )
        system_message = await kernel_prompt_template.render(kernel, arguments)
        chat_history.add_system_message(system_message)
        return chat_history

    def _create_config_from_yaml(self, kernel: Kernel) -> "KernelFunction":
        """A temporary method to create a function from the yaml file.
        The yaml.safe_load will be replaced with the proper kernel
        method later."""
        data = yaml.safe_load(self.generate_plan_yaml)
        prompt_template_config = PromptTemplateConfig(**data)
        if "default" in prompt_template_config.execution_settings:
            settings = prompt_template_config.execution_settings.pop("default")
            prompt_template_config.execution_settings[self.service_id] = settings
        return kernel.create_function_from_prompt(
            function_name="create_plan",
            plugin_name="sequential_planner",
            description="Create a plan for the given goal",
            prompt_template_config=prompt_template_config,
        )

    async def _generate_plan(
        self,
        question: str,
        kernel: Kernel,
        arguments: KernelArguments = None,
    ) -> str:
        """Generate the plan for the given question using the kernel"""
        generate_plan_function = self._create_config_from_yaml(kernel)
        functions_manual = await PlannerKernelExtension.get_functions_manual(kernel, arguments)
        generated_plan_args = KernelArguments(
            name_delimiter="-",
            available_functions=functions_manual,
            goal=question,
        )
        generate_plan_result = await kernel.invoke(generate_plan_function, generated_plan_args)
        return str(generate_plan_result)
