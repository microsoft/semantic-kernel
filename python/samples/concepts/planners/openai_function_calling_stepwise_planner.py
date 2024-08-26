# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.core_plugins import MathPlugin, TimePlugin
from semantic_kernel.planners import (
    FunctionCallingStepwisePlanner,
    FunctionCallingStepwisePlannerOptions,
)


async def main():
    kernel = Kernel()

    service_id = "planner"
    kernel.add_service(
        OpenAIChatCompletion(
            service_id=service_id,
        ),
    )

    plugin_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
        "resources",
    )
    kernel.add_plugin(parent_directory=plugin_path, plugin_name="email_plugin")
    kernel.add_plugins({"MathPlugin": MathPlugin(), "TimePlugin": TimePlugin()})

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
        # print(f"\nChat history: {result.chat_history}\n")


if __name__ == "__main__":
    asyncio.run(main())
