# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os

from samples.sk_service_configurator import add_service
from semantic_kernel.kernel import Kernel


async def main():
    # Initialize the kernel
    kernel = Kernel()

    # Add the service to the kernel
    # use_chat: True to use chat completion, False to use text completion
    # use_azure: True to use Azure OpenAI, False to use OpenAI
    kernel = add_service(kernel, use_chat=True)

    script_directory = os.path.dirname(__file__)
    plugins_directory = os.path.join(script_directory, "plugins")
    writer_plugin = kernel.add_plugin(
        parent_directory=plugins_directory, plugin_name="WriterPlugin"
    )

    # Run the ShortPoem function with the Kernel Argument.
    # Kernel arguments can be configured as KernelArguments object
    # or can be passed as kwargs.
    result = await kernel.invoke(writer_plugin["ShortPoem"], input="Hello world")

    print(result)


# Run the main function
if __name__ == "__main__":
    asyncio.run(main())
