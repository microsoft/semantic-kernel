# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.exceptions.kernel_exceptions import KernelException


class SearchException(KernelException):
    """Base class for all Search related exceptions."""

    pass


class SearchResultEmptyError(SearchException):
    """Raised when there are no hits in the search results."""

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
]
