# Copyright (c) Microsoft. All rights reserved.

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    from semantic_kernel.search.kernel_search_result import KernelSearchResult
    from semantic_kernel.search.text_search_result import TextSearchResult


@runtime_checkable
class TextSearch(Protocol):
    """A protocol for text search."""

    async def search(self, query: str, **kwargs: Any) -> "KernelSearchResult[str]":
        """Search for text, returning a KernelSearchResult with a list of strings."""
        ...

    async def get_text_search_result(self, query: str, **kwargs: Any) -> "KernelSearchResult[TextSearchResult]":
        """Search for text, returning a KernelSearchResult with TextSearchResults."""
        ...

    async def get_search_result(self, query: str, **kwargs: Any) -> "KernelSearchResult[Any]":
        """Search for text, returning a KernelSearchResult with the results directly from the service."""
        ...
