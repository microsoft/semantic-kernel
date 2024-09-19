# Copyright (c) Microsoft. All rights reserved.

import logging
from abc import abstractmethod
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any, TypeVar

from semantic_kernel.data.kernel_search_result import KernelSearchResult
from semantic_kernel.data.search_base import SearchBase
from semantic_kernel.data.text_search.text_search_options import TextSearchOptions
from semantic_kernel.functions.kernel_parameter_metadata import KernelParameterMetadata
from semantic_kernel.utils.experimental_decorator import experimental_class

if TYPE_CHECKING:
    from semantic_kernel.data.search_options_base import SearchOptions
    from semantic_kernel.data.text_search.text_search_result import TextSearchResult

TMapInput = TypeVar("TMapInput")

logger = logging.getLogger(__name__)


@experimental_class
class TextSearch(SearchBase):
    """The base class for all text searches."""

    @abstractmethod
    async def get_text_search_result(
        self, options: "SearchOptions | None" = None, **kwargs: Any
    ) -> "KernelSearchResult[TextSearchResult]":
        """Search for text, returning a KernelSearchResult with TextSearchResults."""
        ...

    @property
    def _search_function_map(self) -> dict[str, Callable[..., Awaitable[KernelSearchResult[Any]]]]:
        """Get the search function map.

        Can be overwritten by subclasses.
        """
        return {
            "search": self.search,
            "get_text_search_result": self.get_text_search_result,
            "get_text_search_results": self.get_text_search_result,
            "get_search_result": self.get_search_result,
            "get_search_results": self.get_search_result,
        }

    @property
    def _get_options_class(self) -> type["SearchOptions"]:
        return TextSearchOptions

    @staticmethod
    def _default_parameter_metadata() -> list[KernelParameterMetadata]:
        """Default parameter metadata for text search functions.

        This function should be overridden when necessary.
        """
        return [
            KernelParameterMetadata(
                name="query",
                description="What to search for.",
                type="str",
                is_required=True,
                type_object=str,
            ),
            KernelParameterMetadata(
                name="count",
                description="Number of results to return.",
                type="int",
                is_required=False,
                default_value=2,
                type_object=int,
            ),
            KernelParameterMetadata(
                name="skip",
                description="Number of results to skip.",
                type="int",
                is_required=False,
                default_value=0,
                type_object=int,
            ),
        ]
