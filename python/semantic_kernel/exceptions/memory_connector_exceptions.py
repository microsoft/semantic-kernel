# Copyright (c) Microsoft. All rights reserved.


from semantic_kernel.exceptions.kernel_exceptions import KernelException


class MemoryConnectorException(KernelException):
    """Base class for all memory connector exceptions."""

    pass


class VectorStoreModelException(MemoryConnectorException):
    pass


class VectorStoreModelSerializationException(VectorStoreModelException):
    pass


class VectorStoreModelDeserializationException(VectorStoreModelException):
    pass


class MemoryConnectorInitializationError(MemoryConnectorException):
    """An error occurred while initializing the memory connector."""

    pass


class MemoryConnectorResourceNotFound(MemoryConnectorException):
    """The requested resource was not found in the memory connector."""

    pass


class VectorStoreModelValidationError(VectorStoreModelException):
    pass


__all__ = [
    "MemoryConnectorException",
    "MemoryConnectorInitializationError",
    "MemoryConnectorResourceNotFound",
    "VectorStoreModelDeserializationException",
    "VectorStoreModelException",
    "VectorStoreModelSerializationException",
    "VectorStoreModelValidationError",
]
