# Copyright (c) Microsoft. All rights reserved.

import asyncio

from service_configurator import add_ai_service

import semantic_kernel as sk
from semantic_kernel.core_plugins import MathPlugin


async def main():
    # Initialize the kernel
    kernel = sk.Kernel()

    # Add the service to the kernel
    # use_chat: True to use chat completion, False to use text completion
    kernel = add_ai_service(kernel=kernel, use_chat=True)

    # Import the MathPlugin.
    math_plugin = kernel.import_plugin_from_object(MathPlugin(), plugin_name="MathPlugin")

    result = await kernel.invoke(
        math_plugin["Add"],
        input=5,
        amount=5,
    )

    print(result)


# Run the main function
if __name__ == "__main__":
    asyncio.run(main())
