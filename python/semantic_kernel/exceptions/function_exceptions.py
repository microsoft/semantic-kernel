# Copyright (c) Microsoft. All rights reserved.
from semantic_kernel.exceptions.kernel_exceptions import KernelException


class FunctionException(KernelException):
    """Base class for all function exceptions."""


class FunctionSyntaxError(FunctionException):
    """Base class for all function syntax exceptions."""


class FunctionInitializationError(FunctionException):
    """An error occurred while initializing the function."""

    def __init__(self, message: str):
        """Adds the context of the error to the generic message."""
        super().__init__("KernelFunction failed to initialize: " + message)


class PluginInitializationError(FunctionException):
    """An error occurred while initializing the plugin."""


class PluginInvalidNameError(FunctionSyntaxError):
    """An error occurred while validating the plugin name."""


class FunctionInvalidNameError(FunctionSyntaxError):
    """An error occurred while validating the function name."""


class FunctionInvalidParamNameError(FunctionSyntaxError):
    """An error occurred while validating the function parameter name."""


class FunctionNameNotUniqueError(FunctionSyntaxError):
    """An error occurred while validating the function name."""


class FunctionExecutionException(FunctionException):
    """Base class for all function execution exceptions."""


class FunctionResultError(FunctionException):
    """An error occurred while validating the function result."""


class FunctionInvalidParameterConfiguration(FunctionException):
    """An error occurred while validating the function parameter configuration."""


class PromptRenderingException(FunctionException):
    """An error occurred while rendering a prompt."""


__all__ = [
    "FunctionException",
    "FunctionExecutionException",
    "FunctionInitializationError",
    "FunctionInvalidNameError",
    "FunctionInvalidParamNameError",
    "FunctionNameNotUniqueError",
    "FunctionResultError",
    "FunctionSyntaxError",
    "PluginInitializationError",
    "PluginInvalidNameError",
    "PromptRenderingException",
]
