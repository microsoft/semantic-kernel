# Copyright (c) Microsoft. All rights reserved.
import asyncio
import os

from samples.learn_resources.sk_service_configurator import add_service
from semantic_kernel import Kernel
from semantic_kernel.planners.sequential_planner import SequentialPlanner


async def main():
    # <CreatePlanner>
    # Initialize the kernel
    kernel = Kernel()

    # Add the service to the kernel
    # use_chat: True to use chat completion, False to use text completion
    kernel = add_service(kernel=kernel, use_chat=True)

    script_directory = os.path.dirname(__file__)
    plugins_directory = os.path.join(script_directory, "plugins")
    kernel.add_plugin(parent_directory=plugins_directory, plugin_name="MathPlugin")

    planner = SequentialPlanner(kernel=kernel, service_id="default")
    # </CreatePlanner>
    # <RunPlanner>
    goal = "Figure out how much I have if first, my investment of 2130.23 dollars increased by 23%, and then I spend $5 on a coffee"  # noqa: E501

    # Create a plan
    plan = await planner.create_plan(goal)

    # Execute the plan
    result = await plan.invoke(kernel)

    print(f"The goal: {goal}")
    print("Plan results:")
    print(f"I will have: ${result} left over.")
    # </RunPlanner>


# Run the main function
if __name__ == "__main__":
    asyncio.run(main())
