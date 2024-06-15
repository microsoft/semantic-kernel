# Copyright (c) Microsoft. All rights reserved.


from semantic_kernel.exceptions.kernel_exceptions import KernelException


class MemoryConnectorException(KernelException):
    pass


class MemoryConnectorInitializationError(MemoryConnectorException):
    pass


class MemoryConnectorResourceNotFound(MemoryConnectorException):
    pass


__all__ = [
    "MemoryConnectorException",
    "MemoryConnectorInitializationError",
    "MemoryConnectorResourceNotFound",
]
