# Copyright (c) Microsoft. All rights reserved.
import asyncio
import importlib.util
import os

from service_configurator import add_ai_service

import semantic_kernel as sk
from semantic_kernel.planners.sequential_planner import SequentialPlanner


def get_math_plugin():
    script_directory = os.path.dirname(__file__)
    plugins_directory = os.path.join(script_directory, "plugins/MathPlugin")
    file_path = os.path.join(plugins_directory, "math.py")
    module_name = file_path.replace(script_directory, "").replace(os.path.sep, ".")[1:-3]

    # Import the module dynamically using importlib
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    math_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(math_module)

    # Access the Math class
    Math = getattr(math_module, "Math")

    return Math


async def main():
    # Initialize the kernel
    kernel = sk.Kernel()

    # Add the service to the kernel
    # use_chat: True to use chat completion, False to use text completion
    kernel = add_ai_service(kernel=kernel, use_chat=True)

    Math = get_math_plugin()

    # Import the method functions
    _ = kernel.import_plugin_from_object(Math(), "MathPlugin")

    planner = SequentialPlanner(
        kernel=kernel,
        service_id="default",
    )

    ask = "Figure out how much I have if first, my investment of 2130.23 dollars increased by 23%, and then I spend $5 on a coffee" # noqa: E501

    # Create a plan
    plan = await planner.create_plan(ask)

    # Execute the plan
    result = await kernel.invoke(plan)

    print(f"The ask: {ask}")
    print("Plan results:")
    print(f"I will have: ${result} left over.")


# Run the main function
if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
