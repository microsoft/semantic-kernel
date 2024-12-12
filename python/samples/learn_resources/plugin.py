# Copyright (c) Microsoft. All rights reserved.

import asyncio
from typing import Annotated

from semantic_kernel import Kernel
from semantic_kernel.functions import kernel_function


# Let's define a light plugin
class LightPlugin:
    is_on: bool = False

    @kernel_function(
        name="get_state",
        description="Gets the state of the light.",
    )
    def get_state(
        self,
    ) -> Annotated[str, "the output is a string"]:
        """Returns the state result of the light."""
        return "On" if self.is_on else "Off"

    @kernel_function(
        name="change_state",
        description="Changes the state of the light.",
    )
    def change_state(
        self,
        new_state: Annotated[bool, "the new state of the light"],
    ) -> Annotated[str, "the output is a string"]:
        """Changes the state of the light."""
        self.is_on = new_state
        state = self.get_state()
        print(f"The light is now: {state}")
        return state


async def main():
    # Initialize the kernel
    kernel = Kernel()

    light_plugin = kernel.add_plugin(
        LightPlugin(),
        plugin_name="LightPlugin",
    )

    result = await kernel.invoke(light_plugin["get_state"])
    print(f"The light is: {result}")

    print("Changing the light's state...")

    # Kernel Arguments are passed in as kwargs.
    result = await kernel.invoke(light_plugin["change_state"], new_state=True)
    print(f"The light is: {result}")


# Run the main function
if __name__ == "__main__":
    asyncio.run(main())
