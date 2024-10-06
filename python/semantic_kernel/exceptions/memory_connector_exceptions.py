# Copyright (c) Microsoft. All rights reserved.


from semantic_kernel.exceptions.kernel_exceptions import KernelException


class MemoryConnectorException(KernelException):
    """Base class for all memory connector exceptions."""


class VectorStoreModelException(MemoryConnectorException):
    """Base class for all vector store model exceptions."""


class VectorStoreModelSerializationException(VectorStoreModelException):
    """An error occurred while serializing the vector store model."""


class VectorStoreModelDeserializationException(VectorStoreModelException):
    """An error occurred while deserializing the vector store model."""


class MemoryConnectorInitializationError(MemoryConnectorException):
    """An error occurred while initializing the memory connector."""


class MemoryConnectorResourceNotFound(MemoryConnectorException):
    """The requested resource was not found in the memory connector."""


class VectorStoreModelValidationError(VectorStoreModelException):
    """An error occurred while validating the vector store model."""


<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
class VectorStoreSearchError(MemoryConnectorException):
    """An error occurred while searching the vector store model."""

    pass


>>>>>>> main
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
__all__ = [
    "MemoryConnectorException",
    "MemoryConnectorInitializationError",
    "MemoryConnectorResourceNotFound",
    "VectorStoreModelDeserializationException",
    "VectorStoreModelException",
    "VectorStoreModelSerializationException",
    "VectorStoreModelValidationError",
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
    "VectorStoreSearchError",
>>>>>>> main
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
]
