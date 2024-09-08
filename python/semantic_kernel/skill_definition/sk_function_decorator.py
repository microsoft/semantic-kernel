# Copyright (c) Microsoft. All rights reserved.


def sk_function(description: str):
    """
    Decorator for SK functions.

    Args:
        description -- The description of the function
    """

    def decorator(func):
        func.__sk_function__ = True
        func.__sk_function_description__ = description
        return func

    return decorator
