# Copyright (c) Microsoft. All rights reserved.

import asyncio
<<<<<<< main
from typing import Annotated

from semantic_kernel.exceptions import FunctionExecutionException
=======
import sys
from typing import Union

if sys.version_info >= (3, 9):
    from typing import Annotated
else:
    from typing_extensions import Annotated

>>>>>>> ms/small_fixes
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.kernel_pydantic import KernelBaseModel


class WaitPlugin(KernelBaseModel):
    """WaitPlugin provides a set of functions to wait for a certain amount of time.

    Usage:
        kernel.add_plugin(WaitPlugin(), plugin_name="wait")

    Examples:
        {{wait.wait 5}} => Wait for 5 seconds
    """

<<<<<<< main
    @kernel_function
    async def wait(
        self,
        input: Annotated[
            float | str, "The number of seconds to wait, can be str or float."
        ],
    ) -> None:
        """Wait for a certain number of seconds."""
=======
    @kernel_function(description="Wait for a certain number of seconds.")
    async def wait(
        self, input: Annotated[Union[float, str], "The number of seconds to wait, can be str or float."]
    ) -> None:
>>>>>>> ms/small_fixes
        if isinstance(input, str):
            try:
                input = float(input)
            except ValueError as exc:
<<<<<<< main
                raise FunctionExecutionException(
                    "seconds text must be a number"
                ) from exc
=======
                raise ValueError("seconds text must be a number") from exc
>>>>>>> ms/small_fixes
        await asyncio.sleep(abs(input))
