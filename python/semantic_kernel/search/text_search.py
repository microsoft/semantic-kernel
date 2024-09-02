# Copyright (c) Microsoft. All rights reserved.

import json
import logging
from abc import abstractmethod
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any, Literal, TypeVar

from pydantic import BaseModel, ValidationError

from semantic_kernel.functions import kernel_function
from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.functions.kernel_function_from_method import KernelFunctionFromMethod
from semantic_kernel.functions.kernel_parameter_metadata import KernelParameterMetadata
from semantic_kernel.functions.kernel_plugin import KernelPlugin
from semantic_kernel.prompt_template.kernel_prompt_template import KernelPromptTemplate
from semantic_kernel.search.const import DEFAULT_DESCRIPTION, FilterClauseType
from semantic_kernel.search.kernel_search_result import KernelSearchResult
from semantic_kernel.search.text_search_options import TextSearchOptions
from semantic_kernel.utils.experimental_decorator import experimental_class

if TYPE_CHECKING:
    from semantic_kernel.search.text_search_result import TextSearchResult

TMapInput = TypeVar("TMapInput")

logger = logging.getLogger(__name__)


@experimental_class
class TextSearch:
    """The base class for all text searches."""

    @abstractmethod
    async def search(self, options: TextSearchOptions | None = None, **kwargs: Any) -> "KernelSearchResult[str]":
        """Search for text, returning a KernelSearchResult with a list of strings.

        Args:
            options (TextSearchOptions | None): The search options.
            **kwargs (Any): If options is None, the search options can be passed as keyword arguments.
                They are then used to create a search options object.

        """
        ...

    @abstractmethod
    async def get_text_search_result(
        self, options: TextSearchOptions | None = None, **kwargs: Any
    ) -> "KernelSearchResult[TextSearchResult]":
        """Search for text, returning a KernelSearchResult with TextSearchResults."""
        ...

    @abstractmethod
    async def get_search_result(
        self, options: TextSearchOptions | None = None, **kwargs: Any
    ) -> "KernelSearchResult[Any]":
        """Search for text, returning a KernelSearchResult with the results directly from the service."""
        ...

    def create_plugin(
        self,
        plugin_name: str,
        search_function: Literal["search", "get_search_result"] = "search",
        description: str | None = None,
        options: TextSearchOptions | None = None,
        parameters: list[KernelParameterMetadata] | None = None,
        map_function: Callable[[Any], str] | None = None,
        parameter_to_filter_value_map: dict[str, str] | None = None,
        functions: dict[str, Any] | None = None,
    ) -> KernelPlugin:
        """Create a plugin from a search service and function.

        Args:
            plugin_name: The name of the plugin.
            search_function: The search function to use, either "search" or "get_search_result".
            description: The description of the plugin.
            options: The search options.
            parameters: The parameters for the search function.
            map_function: The function to map search results to strings.
            parameter_to_filter_value_map: A map from parameter names to filter field names.
            functions: A dictionary of function definitions to add to the plugin.
                This expects the same fields as this function (search_function, description,
                options, parameters, map_function, parameter_to_filter_value_map), or falls back to the defaults.
                The key should be the function_name.

        """
        map = {
            "search": self.search,
            "get_search_result": self.get_search_result,
        }
        if not functions:
            return KernelPlugin(
                name=plugin_name,
                description=description,
                functions=[
                    self._create_kernel_function(
                        search_function=map[search_function],
                        options=options,
                        parameters=parameters,
                        plugin_name=plugin_name,
                        function_name=None,
                        description=description,
                        map_function=map_function,
                        parameter_to_filter_value_map=parameter_to_filter_value_map,
                    )
                ],
            )
        kernel_functions = []
        for function_name, function in functions.items():
            kernel_functions.append(
                self._create_kernel_function(
                    search_function=map[function.get("search_function", "search")],
                    options=function.get("options", options),
                    parameters=function.get("parameters", parameters),
                    plugin_name=plugin_name,
                    function_name=function_name,
                    description=function.get("description", description),
                    map_function=function.get("map_function", map_function),
                    parameter_to_filter_value_map=function.get(
                        "parameter_to_filter_value_map", parameter_to_filter_value_map
                    ),
                )
            )
        return KernelPlugin(
            name=plugin_name,
            description=description,
            functions=kernel_functions,
        )

    def _create_kernel_function(
        self,
        search_function: Callable[..., Awaitable[KernelSearchResult[TMapInput]]],
        options: TextSearchOptions | None,
        parameters: list[KernelParameterMetadata] | None,
        plugin_name: str,
        function_name: str | None = None,
        description: str | None = None,
        map_function: Callable[[TMapInput], str] | None = None,
        parameter_to_filter_value_map: dict[str, str] | None = None,
    ) -> KernelFunction:
        """Create a function from a search service."""
        if not map_function:
            map_function = self.default_map_to_string
        if not description:
            description = DEFAULT_DESCRIPTION

        set_options = options.model_dump() if options else {}

        if not parameters:
            parameters = self.default_parameter_metadata()

        @kernel_function(name=function_name or "search", description=description)
        async def search_wrapper(**kwargs: Any) -> str:
            set_options.update(kwargs)
            options = self._set_options_and_filters(set_options, parameters, parameter_to_filter_value_map, **kwargs)

            results = await search_function(options=options)
            return self._map_result_to_strings(results, map_function)

        return KernelFunctionFromMethod(
            method=search_wrapper,
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

    def _set_options_and_filters(
        self,
        options: dict[str, Any],
        parameters: list[KernelParameterMetadata],
        parameter_to_filter_value_map: dict[str, str],
        **kwargs: Any,
    ) -> TextSearchOptions:
        """Set options and filters from keyword arguments."""
        options.update(kwargs)
        search_options = self._create_options(**options)
        if search_options.search_filters is None:
            return search_options
        for filter in search_options.search_filters:
            if filter.clause_type == FilterClauseType.PROMPT:
                filter.value = KernelPromptTemplate.quick_render(template=filter.value, arguments=options)
                continue
            if filter.value is None:
                if filter.field_name in options:
                    filter.value = options.get(filter.field_name)
                    continue
                for param in parameters:
                    target_field = parameter_to_filter_value_map.get(param.name)
                    if target_field == filter.field_name:
                        filter.value = options.get(param.name)
                        if not filter.value:
                            filter.value = param.default_value
                        break
        return search_options

    def _map_result_to_strings(
        self, results: KernelSearchResult[TMapInput], map_function: Callable[[TMapInput], str]
    ) -> list[str]:
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

    def _create_options(self, **kwargs: Any) -> TextSearchOptions:
        try:
            logger.debug(f"Creating TextSearchOptions with kwargs: {kwargs}")
            return TextSearchOptions(**kwargs)
        except ValidationError:
            return TextSearchOptions()
