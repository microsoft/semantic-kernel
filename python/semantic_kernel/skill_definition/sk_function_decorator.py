# Copyright (c) Microsoft. All rights reserved.


def sk_function(
    *,
    description: str = "",
    name: str = None,
    input_description: str = None,
    input_default_value: str = None
):
    """
    Decorator for SK functions.

    Args:
        description -- The description of the function
        name -- The name of the function
        input_description -- The description of the input
        input_default_value -- The default value of the input
    """

    def decorator(func):
        func.__sk_function__ = True
        func.__sk_function_description__ = description
        func.__sk_function_name__ = name if name else func.__name__
        func.__sk_function_input_description__ = input_description
        func.__sk_function_input_default_value__ = input_default_value
        return func

    return decorator
