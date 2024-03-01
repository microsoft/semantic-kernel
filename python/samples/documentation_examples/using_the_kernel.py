# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os

from service_configurator import add_service

import semantic_kernel as sk
from semantic_kernel.core_plugins.time_plugin import TimePlugin


async def main():
    # Initialize the kernel
    kernel = sk.Kernel()

    # Add the service to the kernel
    # use_chat: True to use chat completion, False to use text completion
    kernel = add_service(kernel=kernel, use_chat=True)

    # Import the TimePlugin
    time = kernel.import_plugin_from_object(TimePlugin(), "TimePlugin")

    # Import the WriterPlugin from the plugins directory.
    script_directory = os.path.dirname(__file__)
    plugins_directory = os.path.join(script_directory, "plugins")
    writer_plugin = kernel.import_plugin_from_prompt_directory(
        parent_directory=plugins_directory,
        plugin_directory_name="WriterPlugin",
    )

    # Run the current time function
    currentTime = await kernel.invoke(time["today"])
    print(f"The current date is: {currentTime}\n")

    # Run the short poem function with the Kernel Argument
    poemResult = await kernel.invoke(writer_plugin["ShortPoem"], input=str(currentTime))
    print(f"The poem result:\n\n{poemResult}")


# Run the main function
if __name__ == "__main__":
    asyncio.run(main())
