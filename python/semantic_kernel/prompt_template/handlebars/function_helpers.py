# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from semantic_kernel.functions.kernel_arguments import KernelArguments
    from semantic_kernel.functions.kernel_function import KernelFunction
    from semantic_kernel.kernel import Kernel


logger: logging.Logger = logging.getLogger(__name__)


def create_helper_from_function(
    function: "KernelFunction", kernel: "Kernel", base_arguments: "KernelArguments"
) -> Callable:
    def func(this, *args, **kwargs):
        arguments = base_arguments.copy()
        arguments.update(kwargs)

        logger.debug(
            f"Invoking function {function.metadata.fully_qualified_name} with args: {args} and kwargs: {kwargs} and this: {this}."
        )
        return asyncio.run(function.invoke(kernel=kernel, arguments=arguments))

    return func
