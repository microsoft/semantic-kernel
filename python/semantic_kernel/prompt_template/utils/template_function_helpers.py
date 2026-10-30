# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
from collections.abc import Callable
from html import escape
from typing import TYPE_CHECKING, Any

import nest_asyncio

from semantic_kernel.exceptions import FunctionExecutionException
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.prompt_template.const import (
    HANDLEBARS_TEMPLATE_FORMAT_NAME,
    JINJA2_TEMPLATE_FORMAT_NAME,
    TEMPLATE_FORMAT_TYPES,
)

if TYPE_CHECKING:
    from semantic_kernel.functions.kernel_function import KernelFunction
    from semantic_kernel.kernel import Kernel


logger: logging.Logger = logging.getLogger(__name__)

# Parameters that the kernel injects when invoking a function. They cannot be supplied
# positionally from a template because they are not part of the template-facing signature.
_INJECTED_FUNCTION_PARAMETER_NAMES = frozenset({"kernel", "service", "execution_settings", "arguments"})


def _map_positional_arguments(function: "KernelFunction", positional_args: tuple[Any, ...]) -> dict[str, Any]:
    """Map positional template arguments to the function's template-facing parameters."""
    parameter_names = [
        parameter.name
        for parameter in function.parameters
        if parameter.name is not None
        and (function.metadata.is_prompt or parameter.name not in _INJECTED_FUNCTION_PARAMETER_NAMES)
    ]
    if len(positional_args) > len(parameter_names):
        raise FunctionExecutionException(
            f"Function '{function.fully_qualified_name}' accepts at most {len(parameter_names)} positional "
            f"argument(s), but {len(positional_args)} were provided."
        )
    return dict(zip(parameter_names, positional_args))


def create_template_helper_from_function(
    function: "KernelFunction",
    kernel: "Kernel",
    base_arguments: "KernelArguments",
    template_format: TEMPLATE_FORMAT_TYPES,
    allow_dangerously_set_content: bool = False,
    enable_async: bool = False,
) -> Callable[..., Any]:
    """Create a helper function for both the Handlebars and Jinja2 templating engines from a kernel function.

    Args:
        function (KernelFunction): The kernel function to create a helper for.
        kernel (Kernel): The kernel to use for invoking the function.
        base_arguments (KernelArguments): The base arguments to use when invoking the function.
        template_format (TEMPLATE_FORMAT_TYPES): The template format to create the helper for.
        allow_dangerously_set_content (bool, optional): Return the content of the function result
            without encoding it or not.
        enable_async (bool, optional): Enable async helper function. Defaults to False.
            Currently only works for Jinja2 templates.

    Returns:
        The function with args that are callable by the different templates.

    Raises:
        ValueError: If the template format is not supported.

    """
    if enable_async:
        return _create_async_template_helper_from_function(
            function=function,
            kernel=kernel,
            base_arguments=base_arguments,
            template_format=template_format,
            allow_dangerously_set_content=allow_dangerously_set_content,
        )
    return _create_sync_template_helper_from_function(
        function=function,
        kernel=kernel,
        base_arguments=base_arguments,
        template_format=template_format,
        allow_dangerously_set_content=allow_dangerously_set_content,
    )


def _create_sync_template_helper_from_function(
    function: "KernelFunction",
    kernel: "Kernel",
    base_arguments: "KernelArguments",
    template_format: TEMPLATE_FORMAT_TYPES,
    allow_dangerously_set_content: bool = False,
) -> Callable[..., Any]:
    """Create a helper function for both the Handlebars and Jinja2 templating engines from a kernel function."""
    if template_format not in [JINJA2_TEMPLATE_FORMAT_NAME, HANDLEBARS_TEMPLATE_FORMAT_NAME]:
        raise ValueError(f"Invalid template format: {template_format}")

    if not getattr(asyncio, "_nest_patched", False):
        nest_asyncio.apply()

    def func(*args, **kwargs):
        arguments = KernelArguments()
        if base_arguments and base_arguments.execution_settings:
            arguments.execution_settings = base_arguments.execution_settings  # pragma: no cover
        arguments.update(base_arguments)

        if len(args) > 0 and template_format == HANDLEBARS_TEMPLATE_FORMAT_NAME:
            this = args[0]
            actual_args = args[1:]
        else:
            this = None
            actual_args = args

        if this is not None:
            logger.debug("Handlebars context with `this`.")
        else:
            logger.debug("Jinja2 context or Handlebars context without `this`")

        arguments.update(_map_positional_arguments(function, actual_args))
        arguments.update(kwargs)

        logger.debug(
            "Invoking function %s with positional argument count %d and keyword argument count %d.",
            function.metadata.fully_qualified_name,
            len(actual_args),
            len(kwargs),
        )

        result = asyncio.run(function.invoke(kernel=kernel, arguments=arguments))
        if allow_dangerously_set_content:
            return result
        return escape(str(result))

    return func


def _create_async_template_helper_from_function(
    function: "KernelFunction",
    kernel: "Kernel",
    base_arguments: "KernelArguments",
    template_format: TEMPLATE_FORMAT_TYPES,
    allow_dangerously_set_content: bool = False,
) -> Callable[..., Any]:
    """Create a async helper function for Jinja2 templating engines from a kernel function."""
    if template_format not in [JINJA2_TEMPLATE_FORMAT_NAME]:
        raise ValueError(f"Invalid template format: {template_format}")

    async def func(*args, **kwargs):
        arguments = KernelArguments()
        if base_arguments and base_arguments.execution_settings:
            arguments.execution_settings = base_arguments.execution_settings  # pragma: no cover
        arguments.update(base_arguments)
        arguments.update(_map_positional_arguments(function, args))
        arguments.update(kwargs)
        logger.debug(
            "Invoking function %s with positional argument count %d and keyword argument count %d.",
            function.metadata.fully_qualified_name,
            len(args),
            len(kwargs),
        )
        result = await function.invoke(kernel=kernel, arguments=arguments)
        if allow_dangerously_set_content:
            return result
        return escape(str(result))

    return func
