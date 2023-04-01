# Copyright (c) Microsoft. All rights reserved.

from functools import wraps
from inspect import iscoroutinefunction
from typing import Callable, Optional


def sk_function_context_parameter(
    *, name: str, description: str, default_value: Optional[str] = None
) -> Callable:
    """
    Decorator for SK function context parameters.
    A context parameter is a parameter that the Native Function
    accesses via the Kernel's `context`.

    Example:
    ```
    @sk_function
    @sk_function_context_parameter(
        name="relevance_threshold",
        description="The minimum allowed relevance score...",
    )
    def my_function(...):
        ...

    # Later, to provide the context parameter:
    context["relevance_threshold"] = 0.5
    ```

    :param name: The name of the context parameter.
    :param description: The description of the context parameter.
    :param default_value: The default value of the context parameter.
    :return: The decorated function with context parameters.
    """

    def decorator(func: Callable) -> Callable:
        # Using the wrapper here should preserve
        # the original function's metadata.
        wrapper = None
        if iscoroutinefunction(func):
            # Tricky: If the function is async, we need to
            # use an async wrapper.
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                return await func(*args, **kwargs)

            wrapper = async_wrapper
        else:
            # If the function is not async, we just use
            # a regular wrapper.
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            wrapper = sync_wrapper

        # If the function does not have any context parameters yet,
        # we create an empty list of context parameters.
        if not hasattr(wrapper, "__sk_function_context_parameters__"):
            setattr(wrapper, "__sk_function_context_parameters__", [])

        # We append the context parameter to the list of context parameters.
        # (Including the name, description, and default value.)
        getattr(wrapper, "__sk_function_context_parameters__").append(
            {
                "name": name,
                "description": description,
                "default_value": default_value,
            }
        )
        return wrapper

    return decorator
