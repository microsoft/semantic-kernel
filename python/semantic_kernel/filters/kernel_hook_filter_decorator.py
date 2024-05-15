# # Copyright (c) Microsoft. All rights reserved.
# from __future__ import annotations

# import functools
# import logging
# from inspect import isawaitable
# from types import MethodType
# from typing import Any, Callable, Coroutine

# from semantic_kernel.filters.kernel_filter_context_base import KernelFilterContextBase

# logger = logging.getLogger(__name__)


# def kernel_hook_filter(
#     *,
#     exclude_plugins: list[str] | None = None,
#     include_plugins: list[str] | None = None,
#     exclude_functions: list[str] | None = None,
#     include_functions: list[str] | None = None,
# ) -> Callable[..., Callable[..., Coroutine[Any, Any, None]]]:
#     """Kernel Hook Filter, this allows you to control for which plugin and/or function this hook is executed.

#     If include_* is used, it is assumed others are excluded, and exclude is not checked.
#     Plugins are checked first, before functions.

#     Args:
#         exclude_plugins (list[str]): Plugins to exclude.
#         include_plugins (list[str]): Plugins to include.
#         exclude_functions (list[str]): Functions to exclude.
#         include_functions (list[str]): Functions to include.

#     """

#     def outer_wrapper(
#         func: Callable[..., None],
#     ) -> Callable[..., Coroutine[Any, Any, None]]:
#         if isinstance(func, MethodType):
#             func.__func__.__kernel_hook__ = True  # type: ignore
#             func.__func__.__kernel_hook_filtered__ = not (  # type: ignore
#                 exclude_plugins is None
#                 and include_plugins is None
#                 and exclude_functions is None
#                 and include_functions is None
#             )
#         else:
#             func.__kernel_hook__ = True  # type: ignore
#             func.__kernel_hook_filtered__ = not (  # type: ignore
#                 exclude_plugins is None
#                 and include_plugins is None
#                 and exclude_functions is None
#                 and include_functions is None
#             )

#         @functools.wraps(func)
#         async def wrapper(*args: Any, **kwargs: Any) -> None:
#             if getattr(func, "__kernel_hook_filtered__", False):
#                 context: KernelFilterContextBase = kwargs.get("context", None)
#                 if context:
#                     function_name = context.function.name
#                     plugin_name = context.function.plugin_name
#                     if include_plugins:
#                         if plugin_name not in include_plugins:
#                             logger.debug(f"Plugin {plugin_name} not in {include_plugins}")
#                             return
#                     elif exclude_plugins:
#                         if plugin_name in exclude_plugins:
#                             logger.debug(f"Plugin {plugin_name} in {exclude_plugins}")
#                             return
#                     if include_functions:
#                         if function_name not in include_functions:
#                             logger.debug(f"Function {function_name} not in {include_functions}")
#                             return
#                     elif exclude_functions:
#                         if function_name in exclude_functions:
#                             logger.debug(f"Function {function_name} in {exclude_functions}")
#                             return
#             result = func(*args, **kwargs)
#             if isawaitable(result):
#                 await result

#         return wrapper

#     return outer_wrapper
