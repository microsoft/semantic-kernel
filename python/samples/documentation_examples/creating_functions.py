# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os

from service_configurator import add_service

import semantic_kernel as sk


async def main():
    # Initialize the kernel
    kernel = sk.Kernel()

    # Add the service to the kernel
    # use_chat: True to use chat completion, False to use text completion
    kernel = add_service(kernel=kernel, use_chat=True)

    # Import the MathPlugin.
    script_directory = os.path.dirname(__file__)
    plugins_directory = os.path.join(script_directory, "plugins")
    math_plugin = kernel.import_native_plugin_from_directory(plugins_directory, "MathPlugin")

    result = await kernel.invoke(
        math_plugin["Add"],
        number1=5,
        number2=5,
    )

    print(result)


# Run the main function
if __name__ == "__main__":
    asyncio.run(main())
