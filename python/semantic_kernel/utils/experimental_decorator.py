# Copyright (c) Microsoft. All rights reserved.

import types
from collections.abc import Callable


def experimental_function(func: Callable) -> Callable:
    if isinstance(func, types.FunctionType):
        if func.__doc__:
            func.__doc__ += "\n\nNote: This function is experimental and may change in the future."
        else:
            func.__doc__ = "Note: This function is experimental and may change in the future."

        func.is_experimental = True

    return func


def experimental_class(cls: type) -> type:
    if isinstance(cls, type):
        if cls.__doc__:
            cls.__doc__ += "\n\nNote: This class is experimental and may change in the future."
        else:
            cls.__doc__ = "Note: This class is experimental and may change in the future."

        cls.is_experimental = True

    return cls
