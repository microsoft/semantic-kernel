# Copyright (c) Microsoft. All rights reserved.
from __future__ import annotations

import functools
import logging
from inspect import isawaitable
from types import MethodType
from typing import Any, Callable

from semantic_kernel.hooks.contexts.kernel_hook_context_base import KernelHookContextBase

logger = logging.getLogger(__name__)


def kernel_hook_filter(
    *,
    exclude_plugins: list[str] | None = None,
    include_plugins: list[str] | None = None,
    exclude_functions: list[str] | None = None,
    include_functions: list[str] | None = None,
) -> Callable[..., Callable[..., None]]:
    """Kernel Hook Filter, this allows you to control for which plugin and/or function this hook is executed.

    If include_* is used, it is assumed others are excluded, and exclude is not checked.
    Plugins are checked first, before functions.

    Args:
        exclude_plugins (list[str]): Plugins to exclude.
        include_plugins (list[str]): Plugins to include.
        exclude_functions (list[str]): Functions to exclude.
        include_functions (list[str]): Functions to include.

    """

    def outer_wrapper(
        func: Callable[..., None],
    ) -> Callable[..., None]:
        if isinstance(func, MethodType):
            func.__func__.__kernel_hook__: bool = True
            func.__func__.__kernel_hook_filtered__: bool = not (
                exclude_plugins is None
                and include_plugins is None
                and exclude_functions is None
                and include_functions is None
            )
        else:
            func.__kernel_hook__: bool = True
            func.__kernel_hook_filtered__: bool = not (
                exclude_plugins is None
                and include_plugins is None
                and exclude_functions is None
                and include_functions is None
            )

        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> None:
            if func.__kernel_hook_filtered__:
                context: KernelHookContextBase = kwargs.get("context", None)
                if not context:
                    function_name = context.kernel_function_metadata.name
                    plugin_name = context.kernel_function_metadata.plugin_name
                    if include_plugins:
                        if plugin_name not in include_plugins:
                            logger.debug(f"Plugin {plugin_name} not in {include_plugins}")
                            return
                    elif exclude_plugins:
                        if plugin_name in exclude_plugins:
                            logger.debug(f"Plugin {plugin_name} in {exclude_plugins}")
                            return
                    if include_functions:
                        if function_name not in include_functions:
                            logger.debug(f"Function {function_name} not in {include_functions}")
                            return
                    elif exclude_functions:
                        if function_name in exclude_functions:
                            logger.debug(f"Function {function_name} in {exclude_functions}")
                            return
            result = func(*args, **kwargs)
            if isawaitable(result):
                await result

        return wrapper

    return outer_wrapper
