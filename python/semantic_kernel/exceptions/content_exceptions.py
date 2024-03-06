# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.exceptions.kernel_exceptions import KernelException


class ContentException(KernelException):
    pass


class ContentInitializationError(ContentException):
    pass


class ContentSerializationError(ContentException):
    pass


class ContentAdditionException(ContentException):
    pass


class FunctionCallInvalidNameException(ContentException):
    pass


class FunctionCallInvalidArgumentsException(ContentException):
    pass


__all__ = [
    "ContentException",
    "ContentSerializationError",
    "ContentInitializationError",
    "ContentAdditionException",
    "FunctionCallInvalidNameException",
    "FunctionCallInvalidArgumentsException",
]
