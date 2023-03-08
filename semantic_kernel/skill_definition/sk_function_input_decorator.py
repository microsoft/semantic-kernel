# Copyright (c) Microsoft. All rights reserved.

from functools import wraps


def sk_function_input(*, description: str):
    """
    Decorator for SK function inputs.

    Args:
        description -- The description of the input
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        wrapper.__sk_function_input_description__ = description
        return wrapper

    return decorator
