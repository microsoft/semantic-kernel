# Copyright (c) Microsoft. All rights reserved.


def sk_function_context_parameter(
    *, name: str, description: str, default_value: str = ""
):
    """
    Decorator for SK function context parameters.

    Args:
        name -- The name of the context parameter
        description -- The description of the context parameter
        default_value -- The default value of the context parameter
    """

    def decorator(func):
        if not hasattr(func, "__sk_function_context_parameters__"):
            func.__sk_function_context_parameters__ = []

        func.__sk_function_context_parameters__.append(
            {
                "name": name,
                "description": description,
                "default_value": default_value,
            }
        )
        return func

    return decorator
