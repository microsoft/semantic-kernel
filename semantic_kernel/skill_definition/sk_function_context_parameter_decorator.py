# Copyright (c) Microsoft. All rights reserved.

from functools import wraps
from typing import Optional


def sk_function_context_parameter(
    *, name: str, description: str, default_value: Optional[str] = None
):
    """
    Decorator for SK function context parameters.

    Args:
        name -- The name of the context parameter
        description -- The description of the context parameter
        default_value -- The default value of the context parameter
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        wrapper.__sk_function_context_parameter_name__ = name
        wrapper.__sk_function_context_parameter_description__ = description
        wrapper.__sk_function_context_parameter_default_value__ = default_value
        return wrapper

    return decorator
