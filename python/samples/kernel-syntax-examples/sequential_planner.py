# Copyright (c) Microsoft. All rights reserved.

import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.core_plugins import (
    MathPlugin,
    TextPlugin,
    TimePlugin,
)
from semantic_kernel.planners import SequentialPlanner


async def main():
    kernel = sk.Kernel()
    api_key, org_id = sk.openai_settings_from_dot_env()

    service_id = "gpt-3.5"
    kernel.add_service(
        OpenAIChatCompletion(service_id=service_id, ai_model_id="gpt-3.5-turbo", api_key=api_key, org_id=org_id)
    )
    kernel.import_plugin(MathPlugin(), "math")
    kernel.import_plugin(TimePlugin(), "time")
    kernel.import_plugin(TextPlugin(), "text")
    kernel.import_plugin_from_object(MathPlugin(), "math")
    kernel.import_plugin_from_object(TimePlugin(), "time")
    kernel.import_plugin_from_object(TextPlugin(), "text")

    # create an instance of sequential planner.
    planner = SequentialPlanner(service_id=service_id, kernel=kernel)

    # the ask for which the sequential planner is going to find a relevant function.
    ask = "What day of the week is today, all uppercase?"

    # ask the sequential planner to identify a suitable function from the list of functions available.
    plan = await planner.create_plan(goal=ask)

    # ask the sequential planner to execute the identified function.
    result = await plan.invoke()

    for step in plan._steps:
        print(step.description, ":", step._state.__dict__)

    print("Expected Answer:")
    print(result)
    """
    Output:
    SUNDAY
    """


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
