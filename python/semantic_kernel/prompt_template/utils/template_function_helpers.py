# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
from typing import TYPE_CHECKING, Callable, Literal

import nest_asyncio

from semantic_kernel.prompt_template.const import HANDLEBARS_TEMPLATE_FORMAT_NAME

if TYPE_CHECKING:
    from semantic_kernel.functions.kernel_arguments import KernelArguments
    from semantic_kernel.functions.kernel_function import KernelFunction
    from semantic_kernel.kernel import Kernel


logger: logging.Logger = logging.getLogger(__name__)


def create_template_helper_from_function(
    function: "KernelFunction",
    kernel: "Kernel",
    base_arguments: "KernelArguments",
    template_format: Literal["handlebars", "jinja2"],
) -> Callable:
    """Create a helper function for both the Handlebars and Jinja2 templating engines from a kernel function."""
    if not getattr(asyncio, "_nest_patched", False):
        nest_asyncio.apply()

    def func(*args, **kwargs):
        arguments = base_arguments.copy()
        arguments.update(kwargs)

        if len(args) > 0 and template_format == HANDLEBARS_TEMPLATE_FORMAT_NAME:
            this = args[0]
            actual_args = args[1:]
        else:
            this = None
            actual_args = args

        if this is not None:
            logger.debug(f"Handlebars context with `this`: {this}")
        else:
            logger.debug("Jinja2 context or Handlebars context without `this`")

        logger.debug(
            f"Invoking function {function.metadata.fully_qualified_name} "
            f"with args: {actual_args} and kwargs: {kwargs} and this: {this}."
        )

        return asyncio.run(function.invoke(kernel=kernel, arguments=arguments))

    return func
