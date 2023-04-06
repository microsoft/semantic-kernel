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
        def _cleanup_name(name: str) -> str:
            """
            Removes a trailing _async from the function name.
            """
            if name.endswith("_async"):
                return name[:-6]
            return name

        # We'll also want to cleanup the function's docstring
        def _cleanup_doc(doc: str) -> str:
            """
            We want to take the docstring of the function,
            strip it of whitespace, and take everything up
            to the first completely blank line
            """
            # Empty/no doc --> empty description
            if not doc:
                return ""
            # Get lines (strip spacing)
            lines = [line.strip() for line in doc.splitlines()]
            # Trim empty lines at start
            while lines and not lines[0]:
                lines.pop(0)
            # Take everything up to the first completely blank line
            description = ""
            for line in lines:
                if not line:
                    break
                description += line + " "
            return description.strip()

        # Switched to setattr to make the type checker happy.
        setattr(wrapper, "__sk_function__", True)
        setattr(wrapper, "__sk_function_name__", name or _cleanup_name(func.__name__))
        setattr(
            wrapper,
            "__sk_function_description__",
            description or _cleanup_doc(func.__doc__),
        )
        setattr(wrapper, "__sk_function_input_description__", input_description)
        setattr(wrapper, "__sk_function_input_default_value__", input_default_value)
        return wrapper

    return decorator
