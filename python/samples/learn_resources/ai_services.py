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

    script_directory = os.path.dirname(__file__)
    plugins_directory = os.path.join(script_directory, "plugins")
    writer_plugin = kernel.import_plugin_from_prompt_directory(
        parent_directory=plugins_directory,
        plugin_directory_name="WriterPlugin",
    )

    # Run the ShortPoem function with the Kernel Argument.
    # Kernel arguments can be configured as KernelArguments object
    # or can be passed as kwargs.
    result = await kernel.invoke(writer_plugin["ShortPoem"], input="Hello world")

    print(result)


# Run the main function
if __name__ == "__main__":
    asyncio.run(main())
