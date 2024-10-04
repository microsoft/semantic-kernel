# Copyright (c) Microsoft. All rights reserved.
import asyncio
import os

from service_configurator import add_service

import semantic_kernel as sk
from semantic_kernel.planners.sequential_planner import SequentialPlanner


async def main():
    # Initialize the kernel
    kernel = sk.Kernel()

    # Add the service to the kernel
    # use_chat: True to use chat completion, False to use text completion
    kernel = add_service(kernel=kernel, use_chat=True)

    script_directory = os.path.dirname(__file__)
    plugins_directory = os.path.join(script_directory, "plugins")
    kernel.import_native_plugin_from_directory(plugins_directory, "MathPlugin")

    planner = SequentialPlanner(
        kernel=kernel,
        service_id="default",
    )

    goal = "Figure out how much I have if first, my investment of 2130.23 dollars increased by 23%, and then I spend $5 on a coffee"  # noqa: E501

    # Create a plan
    plan = await planner.create_plan(goal)

    # Execute the plan
    result = await kernel.invoke(plan)

    print(f"The goal: {goal}")
    print("Plan results:")
    print(f"I will have: ${result} left over.")


# Run the main function
if __name__ == "__main__":
    asyncio.run(main())
