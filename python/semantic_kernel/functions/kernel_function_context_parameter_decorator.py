# Copyright (c) Microsoft. All rights reserved.
import logging

logger = logging.getLogger(__name__)


def kernel_function_context_parameter(
    *, name: str, description: str, default_value: str = "", type: str = "string", required: bool = False
):
    """
    Decorator for kernel function context parameters.

    Args:
        name -- The name of the context parameter
        description -- The description of the context parameter
        default_value -- The default value of the context parameter
        type -- The type of the context parameter, used for function calling
        required -- Whether the context parameter is required

    """

    def decorator(func):
        logger.warning(
            "This class has been depricated, use the 'kernel_function' decorator and Annotated parameters instead."
        )
        return func

    return decorator
