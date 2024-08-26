# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.exceptions.kernel_exceptions import KernelException


class ContentException(KernelException):
    """Base class for all content exceptions."""


class ContentInitializationError(ContentException):
    """An error occurred while initializing the content."""


class ContentSerializationError(ContentException):
    """An error occurred while serializing the content."""


class ContentAdditionException(ContentException):
    """An error occurred while adding content."""


class FunctionCallInvalidNameException(ContentException):
    """An error occurred while validating the function name."""


class FunctionCallInvalidArgumentsException(ContentException):
    """An error occurred while validating the function arguments."""


__all__ = [
    "ContentAdditionException",
    "ContentException",
    "ContentInitializationError",
    "ContentSerializationError",
    "FunctionCallInvalidArgumentsException",
    "FunctionCallInvalidNameException",
]
