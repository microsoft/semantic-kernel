# Copyright (c) Microsoft. All rights reserved.

import json
import logging
from abc import ABC
from collections.abc import Awaitable, Callable, Sequence
from copy import deepcopy
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from semantic_kernel.data.const import DEFAULT_DESCRIPTION
from semantic_kernel.data.kernel_search_results import KernelSearchResults
from semantic_kernel.data.search_options import SearchOptions
from semantic_kernel.exceptions.search_exceptions import SearchResultEmptyError
from semantic_kernel.functions import kernel_function
from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.functions.kernel_function_from_method import KernelFunctionFromMethod
from semantic_kernel.functions.kernel_parameter_metadata import KernelParameterMetadata
from semantic_kernel.utils.experimental_decorator import experimental_class

TMapInput = TypeVar("TMapInput")

logger = logging.getLogger(__name__)


@experimental_class
class SearchBase(ABC):
    """The base class for all text searches."""

    # region: Public methods

    def create_kernel_function(
        self,
        search_function: str,
        options: SearchOptions | None,
        parameters: list[KernelParameterMetadata] | None = None,
        return_parameter: KernelParameterMetadata | None = None,
        function_name: str = "search",
        description: str = DEFAULT_DESCRIPTION,
        map_function: Callable[[TMapInput], str] | None = None,
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
            map_function: The function to map the search results to strings.
            update_options_function: A function to create search options.

        """
        search_func = self._search_function_map.get(search_function)
        if not search_func:
            raise ValueError(f"Search function '{search_function}' not found.")

        @kernel_function(name=function_name, description=description)
        async def search_wrapper(**kwargs: Any) -> Sequence[str]:
            search_text = kwargs.get("search_text") or kwargs.get("query")
            query = search_text
            vector = kwargs.get("vector")
            inner_options = self._create_options(deepcopy(options), **kwargs)
            if update_options_function:
                search_text, query, vector, inner_options = update_options_function(
                    search_text, query, vector, inner_options, kwargs
                )
            try:
                results = await search_func(
                    search_text=search_text,
                    query=query,
                    vector=vector,
                    options=inner_options,
                )
            except SearchResultEmptyError:
                return ["No results found for this query"]
            return await self._map_result_to_strings(results, map_function)

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
        self, results: KernelSearchResults[TMapInput], map_function: Callable[[TMapInput], str] | None = None
    ) -> list[str]:
        """Map search results to strings."""
        if not map_function:
            map_function = self._default_map_to_string
        return [map_function(result) async for result in results.results]

    @staticmethod
    def _default_map_to_string(result: Any) -> str:
        """Default mapping function for text search results."""
        if isinstance(result, BaseModel):
            return result.model_dump_json()
        return result if isinstance(result, str) else json.dumps(result)

    # region: Abstract and Overridable methods

    @staticmethod
    def _default_parameter_metadata() -> list[KernelParameterMetadata]:
        """Default parameter metadata for text search functions.

        This function should be overridden by subclasses.
        """
        return []

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

    @property
    def _get_options_class(self) -> type[SearchOptions]:
        return SearchOptions

    @property
    def _search_function_map(self) -> dict[str, Callable[..., Awaitable[KernelSearchResults[Any]]]]:
        """Get the search function map.

        Can be overwritten by subclasses.
        """
        return {}
