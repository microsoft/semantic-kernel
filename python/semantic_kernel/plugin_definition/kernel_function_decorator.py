# Copyright (c) Microsoft. All rights reserved.


from functools import wraps
from inspect import isawaitable
from typing import Callable

from semantic_kernel.orchestration.function_result import FunctionResult
from semantic_kernel.orchestration.kernel_arguments import KernelArguments


def kernel_function(
    *,
    description: str = "",
    name: str = "",
    input_description: str = "",
    input_default_value: str = "",
):
    """
    Decorator for kernel functions.

    Args:
        description -- The description of the function
        name -- The name of the function
        input_description -- The description of the input
        input_default_value -- The default value of the input
    """

    def decorator(func: Callable):
        func.__kernel_function__ = True
        func.__kernel_function_description__ = description or ""
        func.__kernel_function_name__ = name or func.__name__
        func.__kernel_function_input_description__ = input_description or ""
        func.__kernel_function_input_default_value__ = input_default_value or ""

        @wraps(func)
        async def wrapper(*args, **kwargs):
            k_args = None
            for arg in args:
                if isinstance(arg, KernelArguments):
                    k_args = arg
                    break
            if not k_args:
                for arg in kwargs.values():
                    if isinstance(arg, KernelArguments):
                        k_args = arg
                        break
            if k_args:
                result = func(**k_args)
                if isawaitable(result):
                    result = await result
            else:
                result = None
            if isinstance(result, FunctionResult):
                return result
            return FunctionResult(function=func, value=result)

        return wrapper

    return decorator
