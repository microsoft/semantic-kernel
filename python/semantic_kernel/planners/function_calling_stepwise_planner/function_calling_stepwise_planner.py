# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os
import yaml
from copy import copy
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.planners.function_calling_stepwise_planner.function_calling_stepwise_planner_options import FunctionCallingStepwisePlannerOptions
from semantic_kernel.kernel import Kernel
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.contents.chat_history import ChatHistory
import sys 
from typing import Any, Callable, Optional
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig
from semantic_kernel.planners.sequential_planner.sequential_planner_extensions import SequentialPlannerKernelExtension
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.prompt_template.kernel_prompt_template import KernelPromptTemplate
from semantic_kernel.connectors.ai.chat_completion_client_base import (
    ChatCompletionClientBase,
)
from semantic_kernel.contents.chat_message_content import ChatMessageContent
if sys.version_info >= (3, 9):
    from typing import Annotated
else:
    from typing_extensions import Annotated

CUR_DIR = os.path.dirname(os.path.realpath(__file__))
PLAN_YAML_FILE_PATH = os.path.join(CUR_DIR, "generate_plan.yaml")
STEP_PROMPT_FILE_PATH = os.path.join(CUR_DIR, "step_prompt.txt")

STEPWISE_PLANNER_PLUGIN_NAME = "StepwisePlanner_Excluded"

STEPWISE_USER_MESSAGE = (
    "Perform the next step of the plan if there is more work to do."
    "When you have reached a final answer, use the UserInteraction-SendFinalAnswer"
    "function to communicate this back to the user."
)

def read_file(file_path: str) -> str:
    with open(file_path, "r") as file:
        return file.read()
    
class UserInteraction:
    @kernel_function(description="The final answer to return to the user", name="SendFinalAnswer")
    def send_final_answer(self, answer: Annotated[str, "The final answer"]) -> str:
        return "Thanks"

class FunctionCallingStepwisePlanner(KernelBaseModel):

    service_id: str
    options: FunctionCallingStepwisePlannerOptions
    generate_plan_yaml: str
    step_prompt: str

    def __init__(self, service_id: str, options: Optional[FunctionCallingStepwisePlannerOptions] = None):

        options = options or FunctionCallingStepwisePlannerOptions()
        generate_plan_yaml = options.get_initial_plan() if options.get_initial_plan else read_file(PLAN_YAML_FILE_PATH)
        step_prompt = options.get_step_prompt() if options.get_step_prompt else read_file(STEP_PROMPT_FILE_PATH)
        options.excluded_plugins.add(STEPWISE_PLANNER_PLUGIN_NAME)

        super().__init__(
            service_id=service_id,
            options=options, 
            generate_plan_yaml=generate_plan_yaml, 
            step_prompt=step_prompt
        )

    async def execute(
        self,
        kernel: Kernel,
        question: str,
    ) -> None:
        # TODO error handling for question
        if not question:
            raise ValueError("question cannot be empty")

        chat_completion = kernel.get_service(service_id=self.service_id)
        prompt_execution_settings = self.options.execution_settings or chat_completion.get_prompt_execution_settings_class()

        # Clone the kernel so that we can add planner-specific plugins without affecting the original kernel instance
        cloned_kernel = copy(kernel)
        cloned_kernel.import_plugin_from_object(UserInteraction(), "UserInteraction")

        # Create and invoke a kernel function to generate the initial plan
        initial_plan = await self.generate_plan(question, cloned_kernel)

        chat_history_for_steps = await self.build_chat_history_for_step(question, initial_plan, cloned_kernel)

        for i in range(self.options.max_iterations):
            # sleep for a bit to avoid rate limiting
            if i > 0:
                await asyncio.sleep(self.options.min_iteration_time_ms)

        # For each step, request another completion to select a function for that step 
        chat_history_for_steps.add_user_message(STEPWISE_USER_MESSAGE)
        chat_result = await self.get_completion_with_functions(chat_history_for_steps, cloned_kernel, chat_completion, prompt_execution_settings)

    async def get_completion_with_functions(
        self,
        chat_history: ChatHistory,
        kernel: Kernel,
        chat_completion: ChatCompletionClientBase,
        prompt_execution_settings: Any,
    ) -> ChatMessageContent:
        await 

    async def build_chat_history_for_step(
        self,
        goal: str,
        initial_plan: str,
        kernel: Kernel,
    ) -> ChatHistory:
        chat_history = ChatHistory()
        arguments = KernelArguments(
            goal=goal,
            initial_plan=initial_plan,
        )
        prompt_template_config = PromptTemplateConfig(
            template=self.step_prompt,
        )
        kernel_prompt_template = KernelPromptTemplate(prompt_template_config=prompt_template_config)
        system_message = await kernel_prompt_template.render(kernel, arguments)
        chat_history.add_system_message(system_message)
        return chat_history

    def create_config_from_yaml(self, kernel: Kernel) -> "KernelFunction":
        # Temp method
        data = yaml.safe_load(self.generate_plan_yaml)
        # Create an instance of PromptTemplateConfig with the loaded data
        prompt_template_config = PromptTemplateConfig(**data)
        if 'default' in prompt_template_config.execution_settings:
            settings = prompt_template_config.execution_settings.pop("default")
            prompt_template_config.execution_settings[self.service_id] = settings
        return kernel.create_function_from_prompt(prompt_template_config=prompt_template_config)

    async def generate_plan(
        self,
        question: str,
        kernel: Kernel,
    ) -> str:
        generate_plan_function = self.create_config_from_yaml(kernel)
        functions_manual = await SequentialPlannerKernelExtension.get_functions_manual(kernel)
        generated_plan_args = KernelArguments(
            name_delimiter="-",
            available_functions=functions_manual,
            goal=question,
        )
        generate_plan_result = await kernel.invoke(generate_plan_function, generated_plan_args)
        return str(generate_plan_result)