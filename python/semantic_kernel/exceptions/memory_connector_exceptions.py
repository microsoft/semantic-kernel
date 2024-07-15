# Copyright (c) Microsoft. All rights reserved.


from semantic_kernel.exceptions.kernel_exceptions import KernelException


class MemoryConnectorException(KernelException):
    pass


class VectorStoreModelException(MemoryConnectorException):
    pass


class VectorStoreModelSerializationException(VectorStoreModelException):
    pass


class VectorStoreModelDeserializationException(VectorStoreModelException):
    pass


class MemoryConnectorInitializationError(MemoryConnectorException):
    pass


class MemoryConnectorResourceNotFound(MemoryConnectorException):
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
