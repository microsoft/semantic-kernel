# Copyright (c) Microsoft. All rights reserved.
import os
from copy import copy
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.planners.function_calling_stepwise_planner.function_calling_stepwise_planner_options import FunctionCallingStepwisePlannerOptions
from semantic_kernel.kernel import Kernel
from semantic_kernel.functions.kernel_function_decorator import kernel_function
import sys 
from typing import Any, Callable, Optional

if sys.version_info >= (3, 9):
    from typing import Annotated
else:
    from typing_extensions import Annotated

CUR_DIR = os.path.dirname(os.path.realpath(__file__))
PLAN_YAML_FILE_PATH = os.path.join(CUR_DIR, "generate_plan.yaml")
STEP_PROMPT_FILE_PATH = os.path.join(CUR_DIR, "step_prompt.txt")

STEPWISE_PLANNER_PLUGIN_NAME = "StepwisePlanner_Excluded"

def read_file(file_path: str) -> str:
    with open(file_path, "r") as file:
        return file.read()
    
class UserInteraction:
    @kernel_function(description="The final answer to return to the user", name="sendFinalAnswer")
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

    async def execution(
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
