# Copyright (c) Microsoft. All rights reserved.

from functools import wraps
from inspect import iscoroutinefunction
from typing import Callable, Optional


def sk_function(
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    input_description: Optional[str] = None,
    input_default_value: Optional[str] = None
) -> Callable:
    """
    Decorator used to define a Native Function in a Skill.
    (Native Functions, in Semantic Kernel, are functions
    decorated with this decorator and defined in a class,
    the parent class is a "Skill" and the skill/functions
    can be imported into the Kernel via: `Kernel.import_skill(...)`.)

    :param name: Name of the function. If not provided,
        the name of the decorated function will be used.
    :param description: Description of the function. If not provided,
        the docstring of the decorated function will be used.
    :param input_description: Description of the input parameter.
    :param input_default_value: Default value of the input parameter.

    :return: The decorated function (a Native Function, in SK terms).
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

        # We may want to cleanup the name of the function,
        # for example, if the function is named `read_async`,
        # we want to remove the `_async` suffix. (So, in a
        # Prompt Template, we can call `read` instead of
        # `read_async`)
        def _cleanup(name: str) -> str:
            """
            Removes a trailing _async from the function name.
            """
            if name.endswith("_async"):
                return name[:-6]
            return name

        # Switched to setattr to make the type checker happy.
        setattr(wrapper, "__sk_function__", True)
        setattr(wrapper, "__sk_function_name__", name or _cleanup(func.__name__))
        setattr(wrapper, "__sk_function_description__", description or func.__doc__)
        setattr(wrapper, "__sk_function_input_description__", input_description)
        setattr(wrapper, "__sk_function_input_default_value__", input_default_value)
        return wrapper

    return decorator
