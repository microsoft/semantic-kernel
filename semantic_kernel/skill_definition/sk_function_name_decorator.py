# Copyright (c) Microsoft. All rights reserved.


def sk_function_name(name: str):
    """
    Decorator for SK function names.

    Args:
        name -- The name of the function
    """

    def decorator(func):
        func.__sk_function_name__ = name
        return func

    return decorator
