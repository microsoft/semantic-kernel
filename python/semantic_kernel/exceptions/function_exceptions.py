# Copyright (c) Microsoft. All rights reserved.
from semantic_kernel.exceptions.kernel_exceptions import KernelException


class FunctionException(KernelException):
    pass


class FunctionSyntaxError(FunctionException):
    pass


class FunctionInitializationError(FunctionException):
    def __init__(self, message: str):
        super().__init__("KernelFunction failed to initialize: " + message)


class PluginInitializationError(FunctionException):
    pass


class PluginInvalidNameError(FunctionSyntaxError):
    pass


class FunctionInvalidNameError(FunctionSyntaxError):
    pass


class FunctionInvalidParamNameError(FunctionSyntaxError):
    pass


class FunctionNameNotUniqueError(FunctionSyntaxError):
    pass


class FunctionExecutionException(FunctionException):
    pass


class FunctionResultError(FunctionException):
    pass


__all__ = [
    "FunctionException",
    "FunctionInitializationError",
    "FunctionInvalidParamNameError",
    "FunctionInvalidNameError",
    "FunctionNameNotUniqueError",
    "FunctionSyntaxError",
    "PluginInitializationError",
    "PluginInvalidNameError",
    "FunctionExecutionException",
    "FunctionResultError",
]
