# Copyright (c) Microsoft. All rights reserved.

from functools import wraps


def sk_function_name(name: str):
    """
    Decorator for SK function names.

    Args:
        name -- The name of the function
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        wrapper.__sk_function_name__ = name
        return wrapper

    return decorator
