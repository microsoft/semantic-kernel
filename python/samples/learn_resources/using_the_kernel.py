# Copyright (c) Microsoft. All rights reserved.

# <NecessaryPackages>
import asyncio
import os

from samples.sk_service_configurator import add_service
from semantic_kernel import Kernel

# </NecessaryPackages>


async def main():
    # Initialize the kernel
    # <KernelCreation>
    kernel = Kernel()
    # Add the service to the kernel
    # use_chat: True to use chat completion, False to use text completion
    kernel = add_service(kernel, use_chat=True)
    # </KernelCreation>

    # <InvokeUtcNow>
    # Import the TimePlugin and add it to the kernel
    from semantic_kernel.core_plugins import TimePlugin

    time = kernel.add_plugin(TimePlugin(), "TimePlugin")

    # Invoke the Today function
    current_time = await kernel.invoke(time["today"])
    print(f"The current date is: {current_time}\n")
    # </InvokeUtcNow>

    # <InvokeShortPoem>
    # Import the WriterPlugin from the plugins directory.
    script_directory = os.path.dirname(__file__)
    plugins_directory = os.path.join(script_directory, "plugins")
    kernel.add_plugin(parent_directory=plugins_directory, plugin_name="WriterPlugin")
    # Run the short poem function with the Kernel Argument
    poem_result = await kernel.invoke(
        function_name="ShortPoem", plugin_name="WriterPlugin", input=str(current_time)
    )
    print(f"The poem result:\n\n{poem_result}")
    # </InvokeShortPoem>


# Run the main function
if __name__ == "__main__":
    asyncio.run(main())
