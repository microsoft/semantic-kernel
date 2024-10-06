# Copyright (c) Microsoft. All rights reserved.

import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.core_plugins import (
    MathPlugin,
    TextPlugin,
    TimePlugin,
)
from semantic_kernel.planners import ActionPlanner


async def main():
    kernel = sk.Kernel()
    api_key, org_id = sk.openai_settings_from_dot_env()
    service_id = "chat-gpt"
    kernel.add_service(
        OpenAIChatCompletion(service_id=service_id, ai_model_id="gpt-3.5-turbo", api_key=api_key, org_id=org_id)
    )

    kernel.import_plugin(MathPlugin(), "math")
    kernel.import_plugin(TimePlugin(), "time")
    kernel.import_plugin(TextPlugin(), "text")
    kernel.import_plugin_from_object(MathPlugin(), "math")
    kernel.import_plugin_from_object(TimePlugin(), "time")
    kernel.import_plugin_from_object(TextPlugin(), "text")

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
    import asyncio

    asyncio.run(main())
