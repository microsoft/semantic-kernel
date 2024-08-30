# Copyright (c) Microsoft. All rights reserved.

import json
from abc import abstractmethod
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

from semantic_kernel.functions import kernel_function
from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.functions.kernel_function_from_method import KernelFunctionFromMethod
from semantic_kernel.functions.kernel_parameter_metadata import KernelParameterMetadata
from semantic_kernel.functions.kernel_plugin import KernelPlugin
from semantic_kernel.search.kernel_search_result import KernelSearchResult
from semantic_kernel.search.text_search_options import TextSearchOptions
from semantic_kernel.utils.experimental_decorator import experimental_class

if TYPE_CHECKING:
    from semantic_kernel.search.text_search_result import TextSearchResult


@experimental_class
class TextSearch:
    """The base class for all text searches."""

    @abstractmethod
    async def search(
        self, query: str, options: TextSearchOptions | None = None, **kwargs: Any
    ) -> "KernelSearchResult[str]":
        """Search for text, returning a KernelSearchResult with a list of strings."""
        ...

    @abstractmethod
    async def get_text_search_result(
        self, query: str, options: TextSearchOptions | None = None, **kwargs: Any
    ) -> "KernelSearchResult[TextSearchResult]":
        """Search for text, returning a KernelSearchResult with TextSearchResults."""
        ...

    @abstractmethod
    async def get_search_result(
        self, query: str, options: TextSearchOptions | None = None, **kwargs: Any
    ) -> "KernelSearchResult[Any]":
        """Search for text, returning a KernelSearchResult with the results directly from the service."""
        ...

    def create_plugin_from_search(
        self,
        plugin_name: str,
        description: str | None = None,
        options: TextSearchOptions | None = None,
        parameters: list[KernelParameterMetadata] | None = None,
        map_function: Callable[[Any], str] | None = None,
    ) -> KernelPlugin:
        """Create a function from a search service."""
        return KernelPlugin(
            name=plugin_name,
            description=description,
            functions=[
                self.create_function_from_search(
                    options,
                    parameters=parameters,
                    plugin_name=plugin_name,
                    description=description,
                    map_function=map_function,
                )
            ],
        )

    def create_function_from_search(
        self,
        options: TextSearchOptions | None,
        parameters: list[KernelParameterMetadata] | None,
        plugin_name: str,
        description: str | None = None,
        map_function: Callable[[Any], str] | None = None,
    ) -> KernelFunction:
        """Create a function from a search service."""
        if not map_function:
            map_function = self.default_map_to_string
        if not description:
            description = "Perform a search for content related to the specified query and return string results"
        if options is None:

            @kernel_function(description=description)
            async def search(query: str, count: int = 2, skip: int = 0) -> str:
                results = await self.search(query, count=count, offset=skip)
                return self._map_to_strings(results, map_function)

            if not parameters:
                parameters = self.default_parameter_metadata()

        else:

            @kernel_function(description=description)
            async def search(query: str) -> str:
                results = await self.search(query, options=options)
                return self._map_to_strings(results, map_function)

            if not parameters:
                parameters = self.default_parameter_metadata()
                # when options are provided, they cannot be passed as parameters by a LLM
                # hence we remove them from the parameters list
                parameters = parameters[:1]

        return KernelFunctionFromMethod(
            method=search,
            plugin_name=plugin_name,
            parameters=parameters,
            return_parameter=KernelParameterMetadata(
                name="results",
                description="The search results.",
                type="list[str]",
                type_object=list,
                is_required=True,
            ),
        )

    def _map_to_strings(self, results: KernelSearchResult, map_function: Callable[[Any], str]) -> list[str]:
        """Map search results to strings."""
        return [map_function(result) for result in results.results]

    @staticmethod
    def default_map_to_string(result: Any) -> str:
        """Default mapping function for text search results."""
        if isinstance(result, BaseModel):
            return result.model_dump_json()
        return result if isinstance(result, str) else json.dumps(result)

    @staticmethod
    def default_parameter_metadata() -> list[KernelParameterMetadata]:
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
