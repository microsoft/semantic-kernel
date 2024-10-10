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


<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
class VectorStoreSearchError(MemoryConnectorException):
    """An error occurred while searching the vector store model."""

    pass


<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
__all__ = [
    "MemoryConnectorException",
    "MemoryConnectorInitializationError",
    "MemoryConnectorResourceNotFound",
    "VectorStoreModelDeserializationException",
    "VectorStoreModelException",
    "VectorStoreModelSerializationException",
    "VectorStoreModelValidationError",
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
    "VectorStoreSearchError",
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
    "VectorStoreSearchError",
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
    "VectorStoreSearchError",
>>>>>>> main
>>>>>>> Stashed changes
]
