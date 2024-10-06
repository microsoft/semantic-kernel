# Copyright (c) Microsoft. All rights reserved.

import asyncio
<<<<<<< Updated upstream
<<<<<<< Updated upstream
from typing import Annotated

from semantic_kernel.exceptions import FunctionExecutionException
=======
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
from typing import Annotated

from semantic_kernel.exceptions import FunctionExecutionException
=======
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
>>>>>>> main
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.kernel_pydantic import KernelBaseModel


class WaitPlugin(KernelBaseModel):
    """WaitPlugin provides a set of functions to wait for a certain amount of time.

    Usage:
        kernel.add_plugin(WaitPlugin(), plugin_name="wait")

    Examples:
        {{wait.wait 5}} => Wait for 5 seconds
    """

<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< main
>>>>>>> main
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    @kernel_function
    async def wait(
        self,
        input: Annotated[
            float | str, "The number of seconds to wait, can be str or float."
        ],
    ) -> None:
        """Wait for a certain number of seconds."""
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
    @kernel_function(description="Wait for a certain number of seconds.")
    async def wait(
        self, input: Annotated[Union[float, str], "The number of seconds to wait, can be str or float."]
    ) -> None:
>>>>>>> ms/small_fixes
>>>>>>> main
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
        if isinstance(input, str):
            try:
                input = float(input)
            except ValueError as exc:
<<<<<<< Updated upstream
<<<<<<< Updated upstream
                raise FunctionExecutionException(
                    "seconds text must be a number"
                ) from exc
=======
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
                raise FunctionExecutionException(
                    "seconds text must be a number"
                ) from exc
=======
<<<<<<< main
                raise FunctionExecutionException(
                    "seconds text must be a number"
                ) from exc
=======
                raise ValueError("seconds text must be a number") from exc
>>>>>>> ms/small_fixes
>>>>>>> main
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
        await asyncio.sleep(abs(input))
