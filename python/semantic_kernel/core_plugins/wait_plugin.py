# Copyright (c) Microsoft. All rights reserved.

import asyncio
import sys
from typing import Union

from semantic_kernel.exceptions import FunctionExecutionException

if sys.version_info >= (3, 9):
    from typing import Annotated
else:
    from typing_extensions import Annotated

from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.kernel_pydantic import KernelBaseModel


class WaitPlugin(KernelBaseModel):
    """
    WaitPlugin provides a set of functions to wait for a certain amount of time.

    Usage:
        kernel.import_plugin_from_object(WaitPlugin(), plugin_name="wait")

    Examples:
        {{wait.wait 5}} => Wait for 5 seconds
    """

    @kernel_function(description="Wait for a certain number of seconds.")
    async def wait(
        self, input: Annotated[Union[float, str], "The number of seconds to wait, can be str or float."]
    ) -> None:
        if isinstance(input, str):
            try:
                input = float(input)
            except ValueError as exc:
                raise FunctionExecutionException("seconds text must be a number") from exc
        await asyncio.sleep(abs(input))
