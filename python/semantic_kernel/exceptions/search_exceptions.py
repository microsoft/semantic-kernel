# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.exceptions.kernel_exceptions import KernelException


class SearchException(KernelException):
    """Base class for all Search related exceptions."""

    pass


class VectorStoreMixinException(SearchException):
    """Raised when a mixin is used without the VectorSearchBase Class."""

    pass


class VectorStoreTextSearchValidationError(SearchException):
    """An error occurred while validating the vector store text search model."""

    pass


class SearchResultEmptyError(SearchException):
    """Raised when there are no hits in the search results."""

    pass


class VectorSearchExecutionException(SearchException):
    """Raised when there is an error executing a VectorSearch function."""

    pass


class VectorSearchOptionsException(SearchException):
    """Raised when invalid options are given to a VectorSearch function."""

    pass


class TextSearchException(SearchException):
    """An error occurred while executing a text search function."""

    pass


class TextSearchOptionsException(SearchException):
    """Raised when invalid options are given to a TextSearch function."""

    pass


__all__ = [
    "SearchException",
    "SearchResultEmptyError",
    "TextSearchException",
    "TextSearchOptionsException",
    "VectorSearchExecutionException",
    "VectorSearchOptionsException",
    "VectorStoreMixinException",
    "VectorStoreTextSearchValidationError",
]
