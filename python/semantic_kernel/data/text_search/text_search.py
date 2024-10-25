# Copyright (c) Microsoft. All rights reserved.

import json
import logging
from abc import abstractmethod
from collections.abc import Awaitable, Callable, Sequence
from copy import deepcopy
from typing import TYPE_CHECKING, Any, TypeVar

from pydantic import BaseModel, ValidationError

from semantic_kernel.data.const import DEFAULT_DESCRIPTION
from semantic_kernel.data.kernel_search_results import KernelSearchResults
from semantic_kernel.data.search_options import SearchOptions
from semantic_kernel.data.text_search.text_search_options import TextSearchOptions
from semantic_kernel.exceptions.search_exceptions import SearchResultEmptyError
from semantic_kernel.functions import kernel_function
from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.functions.kernel_function_from_method import KernelFunctionFromMethod
from semantic_kernel.functions.kernel_parameter_metadata import KernelParameterMetadata
from semantic_kernel.utils.experimental_decorator import experimental_class

if TYPE_CHECKING:
    from semantic_kernel.data.search_options import SearchOptions
    from semantic_kernel.data.text_search.text_search_result import TextSearchResult

TMapInput = TypeVar("TMapInput")

logger = logging.getLogger(__name__)


@experimental_class
class TextSearch:
    """The base class for all text searches."""

    @property
    def _search_function_map(self) -> dict[str, Callable[..., Awaitable[KernelSearchResults[Any]]]]:
        """Get the search function map.

        Can be overwritten by subclasses.
        """
        return {
            "search": self.search,
            "text_search": self.search,
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
                name="top",
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

    @staticmethod
    def _default_return_parameter_metadata() -> KernelParameterMetadata:
        """Default return parameter metadata for text search functions.

        This function should be overridden by subclasses.
        """
        return KernelParameterMetadata(
            name="results",
            description="The search results.",
            type="list[str]",
            type_object=list,
            is_required=True,
        )

    # region: Public methods

    def create_kernel_function(
        self,
        search_function: str,
        options: SearchOptions | None,
        parameters: list[KernelParameterMetadata] | None = None,
        return_parameter: KernelParameterMetadata | None = None,
        function_name: str = "search",
        description: str = DEFAULT_DESCRIPTION,
        string_mapper: Callable[[TMapInput], str] | None = None,
        update_options_function: Callable[
            [Any, Any, Any, SearchOptions, dict[str, Any]], tuple[Any, Any, Any, SearchOptions]
        ]
        | None = None,
    ) -> KernelFunction:
        """Create a function from a search service.

        Args:
            search_function: The search function.
            options: The search options.
            parameters: The parameters for the function.
            return_parameter: The return parameter for the function.
            function_name: The name of the function.
            description: The description of the function.
            string_mapper: The function to map the search results to strings.
                This can be applied to the results from the chosen search function.
                When using the VectorStoreTextSearch and the Search method, a
                string_mapper can be defined there as well, that is separate from this one.
            update_options_function: A function to create search options.

        """
        search_func = self._search_function_map.get(search_function)
        if not search_func:
            raise ValueError(f"Search function '{search_function}' not found.")

        @kernel_function(name=function_name, description=description)
        async def search_wrapper(**kwargs: Any) -> Sequence[str]:
            vectorizable_text = kwargs.get("vectorizable_text")
            query = kwargs.get("query")
            vector = kwargs.get("vector")
            inner_options = self._create_options(deepcopy(options), **kwargs)

            if update_options_function:
                vectorizable_text, query, vector, inner_options = update_options_function(
                    vectorizable_text, query, vector, inner_options, kwargs
                )
            try:
                results = await search_func(
                    vectorizable_text=vectorizable_text,
                    query=query,
                    vector=vector,
                    options=inner_options,
                )
            except SearchResultEmptyError:
                return ["No results found for this query"]
            return await self._map_result_to_strings(results, string_mapper)

        return KernelFunctionFromMethod(
            method=search_wrapper,
            parameters=parameters or self._default_parameter_metadata(),
            return_parameter=return_parameter or self._default_return_parameter_metadata(),
        )

    # endregion
    # region: Private methods

    def _create_options(self, options: SearchOptions | None, **kwargs: Any) -> SearchOptions:
        """Create search options."""
        if options:
            if not isinstance(options, self._get_options_class):
                options = self._get_options_class.model_validate(
                    options.model_dump(exclude_none=True, exclude_defaults=True, exclude_unset=True),
                    strict=False,
                )
            for key, value in kwargs.items():
                if key in options.model_fields:
                    setattr(options, key, value)
            return options
        try:
            logger.debug(f"Creating SearchOptions with kwargs: {kwargs}")
            return self._get_options_class(**kwargs)
        except ValidationError:
            return self._get_options_class()

    async def _map_result_to_strings(
        self, results: KernelSearchResults[TMapInput], string_mapper: Callable[[TMapInput], str] | None = None
    ) -> list[str]:
        """Map search results to strings."""
        if not string_mapper:
            string_mapper = self._default_map_to_string
        return [string_mapper(result) async for result in results.results]

    @staticmethod
    def _default_map_to_string(result: Any) -> str:
        """Default mapping function for text search results."""
        if isinstance(result, BaseModel):
            return result.model_dump_json()
        return result if isinstance(result, str) else json.dumps(result)

    # region: Abstract methods

    @abstractmethod
    async def search(
        self,
        query: str,
        options: "SearchOptions | None" = None,
        **kwargs: Any,
    ) -> "KernelSearchResults[str]":
        """Search for text, returning a KernelSearchResult with a list of strings.

        Args:
            query: The query to search for.
            options: The search options.
            **kwargs: If options is None, the search options can be passed as keyword arguments.
                They are then used to create a search options object.

        """
        ...

    @abstractmethod
    async def get_text_search_result(
        self,
        query: str,
        options: "SearchOptions | None" = None,
        **kwargs: Any,
    ) -> "KernelSearchResults[TextSearchResult]":
        """Search for text, returning a KernelSearchResult with TextSearchResults."""
        ...

    @abstractmethod
    async def get_search_result(
        self,
        query: str,
        options: "SearchOptions | None" = None,
        **kwargs: Any,
    ) -> "KernelSearchResults[Any]":
        """Search for text, returning a KernelSearchResult with the results directly from the service."""
        ...
