# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os

import semantic_kernel as sk
import semantic_kernel.connectors.ai.open_ai as sk_oai
from semantic_kernel.functions.function_result import FunctionResult
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_plugin import KernelPlugin
from semantic_kernel.planners.function_calling_stepwise_planner.function_calling_stepwise_planner import (
    FunctionCallingStepwisePlanner,
)
from semantic_kernel.planners.function_calling_stepwise_planner.function_calling_stepwise_planner_result import (
    FunctionCallingStepwisePlannerResult,
)

kernel = sk.Kernel()
api_key, org_id = sk.openai_settings_from_dot_env()

service_id = "default"

kernel.add_service(
    sk_oai.OpenAIChatCompletion(ai_model_id="gpt-3.5-turbo", service_id=service_id, api_key=api_key, org_id=org_id)
)


async def main() -> None:
    script_directory = os.path.dirname(__file__)
    kernel.import_plugin_from_yaml_directory(
        f"{script_directory}/childrens_book_plugin",
    )

    planner = FunctionCallingStepwisePlanner(service_id=service_id)

    result: FunctionCallingStepwisePlannerResult = await planner.invoke(
        kernel, "Write a cheerful two page story featuring three dogs with each page containing 100 words."
    )

    response = result.final_answer
    print(response)


if __name__ == "__main__":
    asyncio.run(main())
