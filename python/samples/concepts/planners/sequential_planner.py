# Copyright (c) Microsoft. All rights reserved.

import asyncio

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.core_plugins import MathPlugin, TextPlugin, TimePlugin
from semantic_kernel.planners import SequentialPlanner


async def main():
    kernel = Kernel()

    service_id = "gpt-3.5"
    kernel.add_service(
        OpenAIChatCompletion(service_id=service_id, ai_model_id="gpt-3.5-turbo")
    )
    kernel.add_plugins(
        {"math": MathPlugin(), "time": TimePlugin(), "text": TextPlugin()}
    )

    # create an instance of sequential planner.
    planner = SequentialPlanner(service_id=service_id, kernel=kernel)

    # the ask for which the sequential planner is going to find a relevant function.
    ask = "What day of the week is today, all uppercase?"

    # ask the sequential planner to identify a suitable function from the list of functions available.
    plan = await planner.create_plan(goal=ask)

    # ask the sequential planner to execute the identified function.
    result = await plan.invoke(kernel=kernel)

    for step in plan._steps:
        print(step.description, ":", step._state.__dict__)

    print("Expected Answer:")
    print(result)
    """
    Output:
    SUNDAY
    """


if __name__ == "__main__":
    asyncio.run(main())
