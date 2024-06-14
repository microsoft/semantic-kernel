# Copyright (c) Microsoft. All rights reserved.


from semantic_kernel.exceptions.kernel_exceptions import KernelException


class MemoryConnectorException(KernelException):
    pass


class DataModelException(MemoryConnectorException):
    pass


class MemoryConnectorInitializationError(MemoryConnectorException):
    pass


class MemoryConnectorResourceNotFound(MemoryConnectorException):
    pass


__all__ = [
    "DataModelException",
    "MemoryConnectorException",
    "MemoryConnectorInitializationError",
    "MemoryConnectorResourceNotFound",
]
