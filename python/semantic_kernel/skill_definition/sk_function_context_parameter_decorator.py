# Copyright (c) Microsoft. All rights reserved.


def sk_function_context_parameter(
    *,
    name: str,
    description: str,
    default_value: str = "",
    type: str = "string",
    required: bool = True
):
    """
    Decorator for SK function context parameters.

    Args:
        name -- The name of the context parameter
        description -- The description of the context parameter
        default_value -- The default value of the context parameter
        type -- The type of the context parameter, used for function calling
        required -- Whether the context parameter is required for function calling, defaults to True

    """

    def decorator(func):
        if not hasattr(func, "__sk_function_context_parameters__"):
            func.__sk_function_context_parameters__ = []

        func.__sk_function_context_parameters__.append(
            {
                "name": name,
                "description": description,
                "default_value": default_value,
                "type": type_,
                "required": required,
            }
        )
        return func

    return decorator
