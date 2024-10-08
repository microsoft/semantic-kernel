# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
import os
from copy import copy
from typing import Any

import yaml

from semantic_kernel.connectors.ai.function_calling_utils import kernel_function_metadata_to_function_call_format
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_prompt_execution_settings import (
    OpenAIChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.open_ai.services.azure_chat_completion import AzureChatCompletion
from semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion import OpenAIChatCompletion
from semantic_kernel.const import DEFAULT_SERVICE_NAME
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.text_content import TextContent
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
from semantic_kernel.prompt_template.kernel_prompt_template import KernelPromptTemplate
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig

CUR_DIR = os.path.dirname(os.path.realpath(__file__))
PLAN_YAML_FILE_PATH = os.path.join(CUR_DIR, "generate_plan.yaml")
STEP_PROMPT_FILE_PATH = os.path.join(CUR_DIR, "step_prompt.txt")

STEPWISE_PLANNER_PLUGIN_NAME = "StepwisePlanner_Excluded"

STEPWISE_USER_MESSAGE = (
    "Perform the next step of the plan if there is more work to do. "
    "When you have reached a final answer, use the UserInteraction-SendFinalAnswer "
    "function to communicate this back to the user."
)

USER_INTERACTION_SEND_FINAL_ANSWER = "UserInteraction-SendFinalAnswer"

logger: logging.Logger = logging.getLogger(__name__)


class FunctionCallingStepwisePlanner(KernelBaseModel):
    """A Function Calling Stepwise Planner."""

    service_id: str
    options: FunctionCallingStepwisePlannerOptions
    generate_plan_yaml: str
    step_prompt: str

    def __init__(self, service_id: str, options: FunctionCallingStepwisePlannerOptions | None = None):
        """Initialize a new instance of the FunctionCallingStepwisePlanner.

        The FunctionCallingStepwisePlanner is a planner based on top of an OpenAI Chat Completion service
        (whether it be AzureOpenAI or OpenAI), so that we can use tools.

        If the options are configured to use callbacks to get the initial plan and the step prompt,
        the planner will use those provided callbacks to get that information. Otherwise, it will
        read from the default yaml plan file and the step prompt file.

        Args:
            service_id (str): The service id
            options (Optional[FunctionCallingStepwisePlannerOptions], optional): The options for
                the function calling stepwise planner. Defaults to None.
        """
        options = options or FunctionCallingStepwisePlannerOptions()

        if options.get_initial_plan:
            generate_plan_yaml = options.get_initial_plan()
        else:
            with open(PLAN_YAML_FILE_PATH) as f:
                generate_plan_yaml = f.read()

        if options.get_step_prompt:
            step_prompt = options.get_step_prompt()
        else:
            with open(STEP_PROMPT_FILE_PATH) as f:
                step_prompt = f.read()

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
        arguments: KernelArguments | None = None,
        **kwargs: Any,
    ) -> FunctionCallingStepwisePlannerResult:
        """Execute the function calling stepwise planner.

        Args:
            kernel: The kernel instance
            question: The input question
            arguments: (optional) The kernel arguments
            kwargs: (optional) Additional keyword arguments

        Returns:
            FunctionCallingStepwisePlannerResult: The result of the function calling stepwise planner

        Raises:
            PlannerInvalidConfigurationError: If the input question is empty
        """
        if not question:
            raise PlannerInvalidConfigurationError("Input question cannot be empty")

        if not arguments:
            arguments = KernelArguments(**kwargs)

        try:
            chat_completion: OpenAIChatCompletion | AzureChatCompletion = kernel.get_service(service_id=self.service_id)
        except Exception as exc:
            raise PlannerInvalidConfigurationError(
                f"The OpenAI service `{self.service_id}` is not available. Please configure the AI service."
            ) from exc

        if not isinstance(chat_completion, (OpenAIChatCompletion, AzureChatCompletion)):
            raise PlannerInvalidConfigurationError(
                f"The service with id `{self.service_id}` is not an OpenAI based service."
            )

        prompt_execution_settings: OpenAIChatPromptExecutionSettings = (
            self.options.execution_settings
            or chat_completion.instantiate_prompt_execution_settings(service_id=self.service_id)
        )
        if self.options.max_completion_tokens:
            prompt_execution_settings.max_tokens = self.options.max_completion_tokens

        # Clone the kernel so that we can add planner-specific plugins without affecting the original kernel instance
        cloned_kernel = copy(kernel)
        cloned_kernel.add_plugin(UserInteraction(), "UserInteraction")

        # Create and invoke a kernel function to generate the initial plan
        initial_plan = await self._generate_plan(question=question, kernel=cloned_kernel, arguments=arguments)

        chat_history_for_steps = await self._build_chat_history_for_step(
            goal=question, initial_plan=initial_plan, kernel=cloned_kernel, arguments=arguments, service=chat_completion
        )
        prompt_execution_settings.function_choice_behavior = FunctionChoiceBehavior.Auto(
            auto_invoke=False, filters={"excluded_plugins": list(self.options.excluded_plugins)}
        )
        for i in range(self.options.max_iterations):
            # sleep for a bit to avoid rate limiting
            if i > 0:
                await asyncio.sleep(self.options.min_iteration_time_ms / 1000.0)  # convert ms to sec
            # For each step, request another completion to select a function for that step
            chat_history_for_steps.add_user_message(STEPWISE_USER_MESSAGE)
            chat_result = await chat_completion.get_chat_message_contents(
                chat_history=chat_history_for_steps,
                settings=prompt_execution_settings,
                kernel=cloned_kernel,
            )
            chat_result = chat_result[0]
            chat_history_for_steps.add_message(chat_result)

            if not any(isinstance(item, FunctionCallContent) for item in chat_result.items):
                chat_history_for_steps.add_user_message("That function call is invalid. Try something else!")
                continue

            # Try to get the final answer out
            function_call_content = next(
                (
                    item
                    for item in chat_result.items
                    if isinstance(item, FunctionCallContent) and item.name == USER_INTERACTION_SEND_FINAL_ANSWER
                ),
                None,
            )

            if function_call_content is not None:
                args = function_call_content.parse_arguments()
                return FunctionCallingStepwisePlannerResult(
                    final_answer=args.get("answer", ""),
                    chat_history=chat_history_for_steps,
                    iterations=i + 1,
                )

            for item in chat_result.items:
                if not isinstance(item, FunctionCallContent):
                    continue
                try:
                    context = await chat_completion._process_function_call(
                        function_call=item,
                        kernel=cloned_kernel,
                        chat_history=chat_history_for_steps,
                        arguments=arguments,
                        function_call_count=1,
                        request_index=0,
                        function_call_behavior=prompt_execution_settings.function_choice_behavior,
                    )
                    if context is not None:
                        # Only add the function result content to the chat history if the context is present
                        # which means it wasn't added in the _process_function_call method
                        frc = FunctionResultContent.from_function_call_content_and_result(
                            function_call_content=item, result=context.function_result
                        )
                        chat_history_for_steps.add_message(message=frc.to_chat_message_content())
                except Exception as exc:
                    frc = FunctionResultContent.from_function_call_content_and_result(
                        function_call_content=item,
                        result=TextContent(text=f"An error occurred during planner invocation: {exc}"),
                    )
                    chat_history_for_steps.add_message(message=frc.to_chat_message_content())
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
        arguments: KernelArguments,
        service: OpenAIChatCompletion | AzureChatCompletion,
    ) -> ChatHistory:
        """Build the chat history for the stepwise planner."""
        ChatHistory()
        additional_arguments = KernelArguments(
            goal=goal,
            initial_plan=initial_plan,
        )
        arguments.update(additional_arguments)
        kernel_prompt_template = KernelPromptTemplate(
            prompt_template_config=PromptTemplateConfig(
                template=self.step_prompt,
            )
        )
        prompt = await kernel_prompt_template.render(kernel, arguments)
        return ChatHistory.from_rendered_prompt(prompt)

    def _create_config_from_yaml(self, kernel: Kernel) -> "KernelFunction":
        """A temporary method to create a function from the yaml file.

        The yaml.safe_load will be replaced with the proper kernel
        method later.
        """
        data = yaml.safe_load(self.generate_plan_yaml)
        prompt_template_config = PromptTemplateConfig(**data)
        if DEFAULT_SERVICE_NAME in prompt_template_config.execution_settings:
            settings = prompt_template_config.execution_settings.pop(DEFAULT_SERVICE_NAME)
            prompt_template_config.execution_settings[self.service_id] = settings
        return kernel.add_function(
            function_name="create_plan",
            plugin_name="sequential_planner",
            description="Create a plan for the given goal",
            prompt_template_config=prompt_template_config,
        )

    async def _generate_plan(
        self,
        question: str,
        kernel: Kernel,
        arguments: KernelArguments,
    ) -> str:
        """Generate the plan for the given question using the kernel."""
        generate_plan_function = self._create_config_from_yaml(kernel)
        functions_manual = [
            kernel_function_metadata_to_function_call_format(f)
            for f in kernel.get_list_of_function_metadata({
                "excluded_functions": [f"{self.service_id}", "sequential_planner-create_plan"]
            })
        ]
        generated_plan_args = KernelArguments(
            name_delimiter="-",
            available_functions=functions_manual,
            goal=question,
        )
        generated_plan_args.update(arguments)
        generate_plan_result = await kernel.invoke(generate_plan_function, generated_plan_args)
        return str(generate_plan_result)
