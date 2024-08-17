# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.exceptions.kernel_exceptions import KernelException


class ContentException(KernelException):
    """Base class for all content exceptions."""

    pass


class ContentInitializationError(ContentException):
    """An error occurred while initializing the content."""

    pass


class ContentSerializationError(ContentException):
    """An error occurred while serializing the content."""

    pass


class ContentAdditionException(ContentException):
    """An error occurred while adding content."""

    pass


class FunctionCallInvalidNameException(ContentException):
    """An error occurred while validating the function name."""

    pass


class FunctionCallInvalidArgumentsException(ContentException):
    """An error occurred while validating the function arguments."""

    pass


__all__ = [
    "ContentAdditionException",
    "ContentException",
    "ContentInitializationError",
    "ContentSerializationError",
    "FunctionCallInvalidArgumentsException",
    "FunctionCallInvalidNameException",
]
