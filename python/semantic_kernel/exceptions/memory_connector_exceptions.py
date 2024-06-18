# Copyright (c) Microsoft. All rights reserved.


from semantic_kernel.exceptions.kernel_exceptions import KernelException


class MemoryConnectorException(KernelException):
    pass


class DataModelException(MemoryConnectorException):
    pass


class DataModelSerializationException(DataModelException):
    pass


class DataModelDeserializationException(DataModelException):
    pass


class MemoryConnectorInitializationError(MemoryConnectorException):
    pass


class MemoryConnectorResourceNotFound(MemoryConnectorException):
    pass


__all__ = [
    "DataModelDeserializationException",
    "DataModelException",
    "DataModelSerializationException",
    "MemoryConnectorException",
    "MemoryConnectorInitializationError",
    "MemoryConnectorResourceNotFound",
]
