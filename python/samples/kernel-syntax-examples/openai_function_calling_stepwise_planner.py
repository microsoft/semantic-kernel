# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os

import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import (
    OpenAIChatCompletion,
)
from semantic_kernel.core_plugins.math_plugin import MathPlugin
from semantic_kernel.core_plugins.time_plugin import TimePlugin
from semantic_kernel.planners.function_calling_stepwise_planner.function_calling_stepwise_planner import (
    FunctionCallingStepwisePlanner,
)
from semantic_kernel.planners.function_calling_stepwise_planner.function_calling_stepwise_planner_options import (
    FunctionCallingStepwisePlannerOptions,
)


async def main():
    kernel = sk.Kernel()

    service_id = "planner"
    api_key, _ = sk.openai_settings_from_dot_env()
    kernel.add_service(
        OpenAIChatCompletion(
            service_id=service_id,
            ai_model_id="gpt-3.5-turbo-1106",
            api_key=api_key,
        ),
    )

    kernel.import_plugin_from_object(MathPlugin(), "MathPlugin")
    kernel.import_plugin_from_object(TimePlugin(), "TimePlugin")

    cur_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "resources")
    kernel.import_native_plugin_from_directory(cur_dir, "email_plugin")

    questions = [
        "What is the current hour number, plus 5?",
        "What is 387 minus 22? Email the solution to John and Mary.",
        "Write a limerick, translate it to Spanish, and send it to Jane",
    ]

    options = FunctionCallingStepwisePlannerOptions(
        max_iterations=10,
        max_tokens=4000,
    )

    planner = FunctionCallingStepwisePlanner(service_id=service_id, options=options)

    for question in questions:
        result = await planner.invoke(kernel, question)
        print(f"Q: {question}\nA: {result.final_answer}\n")

        # Uncomment the following line to view the planner's process for completing the request
        # print(f"Chat history: {result.chat_history}\n")


if __name__ == "__main__":
    asyncio.run(main())
