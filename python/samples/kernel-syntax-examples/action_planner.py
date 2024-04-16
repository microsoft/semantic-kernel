# Copyright (c) Microsoft. All rights reserved.

import asyncio

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.core_plugins import MathPlugin, TextPlugin, TimePlugin
from semantic_kernel.planners import ActionPlanner
from semantic_kernel.utils.settings import openai_settings_from_dot_env


async def main():
    kernel = Kernel()
    api_key, org_id = openai_settings_from_dot_env()
    service_id = "chat-gpt"
    kernel.add_service(
        OpenAIChatCompletion(service_id=service_id, ai_model_id="gpt-3.5-turbo", api_key=api_key, org_id=org_id)
    )
    kernel.add_plugins({"math": MathPlugin(), "time": TimePlugin(), "text": TextPlugin()})

    # create an instance of action planner.
    planner = ActionPlanner(kernel, service_id)

    # the ask for which the action planner is going to find a relevant function.
    ask = "What is the sum of 110 and 990?"

    # ask the action planner to identify a suitable function from the list of functions available.
    plan = await planner.create_plan(goal=ask)

    # ask the action planner to execute the identified function.
    result = await plan.invoke(kernel)
    print(result)
    """
    Output:
    1100
    """


if __name__ == "__main__":
    asyncio.run(main())
