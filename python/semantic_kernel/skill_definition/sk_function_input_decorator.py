# Copyright (c) Microsoft. All rights reserved.


def sk_function_input(*, description: str, default_value: str = ""):
    """
    Decorator for SK function inputs.

    Args:
        description -- The description of the input
    """

    def decorator(func):
        func.__sk_function_input_description__ = description
        func.__sk_function_input_default_value__ = default_value
        return func

    return decorator
