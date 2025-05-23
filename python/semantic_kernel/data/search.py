# Copyright (c) Microsoft. All rights reserved.

import json
import logging
from abc import ABC, abstractmethod
from collections.abc import AsyncIterable, Callable, Mapping, Sequence
from copy import deepcopy
from typing import Annotated, Any, Generic, Literal, Protocol, TypeVar, overload

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from semantic_kernel.data.const import DEFAULT_DESCRIPTION, DEFAULT_FUNCTION_NAME
from semantic_kernel.exceptions import TextSearchException
from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.functions.kernel_function_from_method import KernelFunctionFromMethod
from semantic_kernel.functions.kernel_parameter_metadata import KernelParameterMetadata
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.kernel_types import OptionalOneOrList
from semantic_kernel.utils.feature_stage_decorator import release_candidate

TSearchOptions = TypeVar("TSearchOptions", bound="SearchOptions")

logger = logging.getLogger(__name__)

# region: Options


@release_candidate
class SearchOptions(ABC, KernelBaseModel):
    """Options for a search.

    When multiple filters are used, they are combined with an AND operator.
    """

    filter: OptionalOneOrList[Callable | str] = None
    skip: Annotated[int, Field(ge=0)] = 0
    top: Annotated[int, Field(gt=0)] = 5
    include_total_count: bool = False

    model_config = ConfigDict(
        extra="allow", populate_by_name=True, arbitrary_types_allowed=True, validate_assignment=True
    )


# region: Results


@release_candidate
class TextSearchResult(KernelBaseModel):
    """The result of a text search."""

    name: str | None = None
    value: str | None = None
    link: str | None = None


TSearchResult = TypeVar("TSearchResult")


@release_candidate
class KernelSearchResults(KernelBaseModel, Generic[TSearchResult]):
    """The result of a kernel search."""

    results: AsyncIterable[TSearchResult]
    total_count: int | None = None
    metadata: Mapping[str, Any] | None = None


# region: Options functions


class DynamicFilterFunction(Protocol):
    """Type definition for the filter update function in Text Search."""

    def __call__(
        self,
        filter: OptionalOneOrList[Callable | str] | None = None,
        parameters: list["KernelParameterMetadata"] | None = None,
        **kwargs: Any,
    ) -> OptionalOneOrList[Callable | str] | None:
        """Signature of the function."""
        ...  # pragma: no cover


def create_options(
    options_class: type["TSearchOptions"],
    options: "SearchOptions | None",
    **kwargs: Any,
) -> "TSearchOptions":
    """Create search options.

    If options are supplied, they are checked for the right type, and the kwargs are used to update the options.

    If options are not supplied, they are created from the kwargs.
    If that fails, an empty options object is returned.

    Args:
        options_class: The class of the options.
        options: The existing options to update.
        **kwargs: The keyword arguments to use to create the options.

    Returns:
        The options of type options_class.

    Raises:
        ValidationError: If the options are not valid.

    """
    # no options give, so just try to create from kwargs
    if not options:
        return options_class.model_validate(kwargs)
    # options are the right class, just update based on kwargs
    if not isinstance(options, options_class):
        # options are not the right class, so create new options
        # first try to dump the existing, if this doesn't work for some reason, try with kwargs only
        additional_kwargs = {}
        try:
            additional_kwargs = options.model_dump(exclude_none=True, exclude_defaults=True, exclude_unset=True)
        except Exception:
            # This is very unlikely to happen, but if it does, we will just create new options.
            # one reason this could happen is if a different class is passed that has no model_dump method
            logger.warning("Options are not valid. Creating new options from just kwargs.")
        kwargs.update(additional_kwargs)
        return options_class.model_validate(kwargs)

    for key, value in kwargs.items():
        if key in options.__class__.model_fields:
            setattr(options, key, value)
    return options


def default_dynamic_filter_function(
    filter: OptionalOneOrList[Callable | str] | None = None,
    parameters: list["KernelParameterMetadata"] | None = None,
    **kwargs: Any,
) -> OptionalOneOrList[Callable | str] | None:
    """The default options update function.

    This function is used to update the query and options with the kwargs.
    You can supply your own version of this function to customize the behavior.

    Args:
        filter: The filter to use for the search.
        parameters: The parameters to use to create the options.
        **kwargs: The keyword arguments to use to update the options.

    Returns:
        OptionalOneOrList[Callable | str] | None: The updated filters

    """
    for param in parameters or []:
        assert param.name  # nosec, when used param name is always set
        if param.name in {"query", "top", "skip", "include_total_count"}:
            continue
        new_filter = None
        if param.name in kwargs:
            new_filter = f"lambda x: x.{param.name} == '{kwargs[param.name]}'"
        elif param.default_value:
            new_filter = f"lambda x: x.{param.name} == '{param.default_value}'"
        if not new_filter:
            continue
        if filter is None:
            filter = new_filter
        elif isinstance(filter, list):
            filter.append(new_filter)
        else:
            filter = [filter, new_filter]

    return filter


# region: Text Search


@release_candidate
class TextSearch:
    """The base class for all text searchers."""

    @property
    def options_class(self) -> type["SearchOptions"]:
        """The options class for the search."""
        return SearchOptions

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

    @overload
    def create_search_function(
        self,
        function_name: str = DEFAULT_FUNCTION_NAME,
        description: str = DEFAULT_DESCRIPTION,
        *,
        output_type: Literal["str"] = "str",
        parameters: list[KernelParameterMetadata] | None = None,
        return_parameter: KernelParameterMetadata | None = None,
        filter: OptionalOneOrList[Callable | str] = None,
        top: int = 5,
        skip: int = 0,
        include_total_count: bool = False,
        filter_update_function: DynamicFilterFunction | None = None,
        string_mapper: Callable[[TSearchResult], str] | None = None,
    ) -> KernelFunction:
        """Create a kernel function from a search function.

        Args:
            output_type: The type of the output, default is "str".
            function_name: The name of the function, to be used in the kernel, default is "search".
            description: The description of the function, a default is provided.
            parameters: The parameters for the function, a list of KernelParameterMetadata.
            return_parameter: The return parameter for the function.
            filter: The filter to use for the search.
            top: The number of results to return.
            skip: The number of results to skip.
            include_total_count: Whether to include the total count of results.
            filter_update_function: A function to update the search filters.
                The function should return the updated filter.
                The default function uses the parameters and the kwargs to update the options.
                Adding equal to filters to the options for all parameters that are not "query".
                As well as adding equal to filters for parameters that have a default value.
            string_mapper: The function to map the search results. (the inner part of the KernelSearchResults type,
                related to which search type you are using) to strings.

        Returns:
            KernelFunction: The kernel function.

        """
        ...

    @overload
    def create_search_function(
        self,
        function_name: str = DEFAULT_FUNCTION_NAME,
        description: str = DEFAULT_DESCRIPTION,
        *,
        output_type: Literal["TextSearchResult"],
        parameters: list[KernelParameterMetadata] | None = None,
        return_parameter: KernelParameterMetadata | None = None,
        filter: OptionalOneOrList[Callable | str] = None,
        top: int = 5,
        skip: int = 0,
        include_total_count: bool = False,
        filter_update_function: DynamicFilterFunction | None = None,
    ) -> KernelFunction:
        """Create a kernel function from a search function.

        Args:
            output_type: The type of the output, in this case TextSearchResult.
            function_name: The name of the function, to be used in the kernel, default is "search".
            description: The description of the function, a default is provided.
            parameters: The parameters for the function, a list of KernelParameterMetadata.
            return_parameter: The return parameter for the function.
            filter: The filter to use for the search.
            top: The number of results to return.
            skip: The number of results to skip.
            include_total_count: Whether to include the total count of results.
            filter_update_function: A function to update the search filters.
                The function should return the updated filter.
                The default function uses the parameters and the kwargs to update the options.
                Adding equal to filters to the options for all parameters that are not "query".
                As well as adding equal to filters for parameters that have a default value.
            string_mapper: The function to map the TextSearchResult  to strings.
                for instance taking the value out of the results and just returning that,
                otherwise a json-like string is returned.

        Returns:
            KernelFunction: The kernel function.

        """
        ...

    @overload
    def create_search_function(
        self,
        function_name: str = DEFAULT_FUNCTION_NAME,
        description: str = DEFAULT_DESCRIPTION,
        *,
        output_type: Literal["Any"],
        parameters: list[KernelParameterMetadata] | None = None,
        return_parameter: KernelParameterMetadata | None = None,
        filter: OptionalOneOrList[Callable | str] = None,
        top: int = 5,
        skip: int = 0,
        include_total_count: bool = False,
        filter_update_function: DynamicFilterFunction | None = None,
    ) -> KernelFunction:
        """Create a kernel function from a search function.

        Args:
            function_name: The name of the function, to be used in the kernel, default is "search".
            description: The description of the function, a default is provided.
            output_type: The type of the output, in this case Any.
                Any means that the results from the store are used directly.
                The string_mapper can then be used to extract certain fields.
            parameters: The parameters for the function, a list of KernelParameterMetadata.
            return_parameter: The return parameter for the function.
            filter: The filter to use for the search.
            top: The number of results to return.
            skip: The number of results to skip.
            include_total_count: Whether to include the total count of results.
            filter_update_function: A function to update the search filters.
                The function should return the updated filter.
                The default function uses the parameters and the kwargs to update the options.
                Adding equal to filters to the options for all parameters that are not "query".
                As well as adding equal to filters for parameters that have a default value.
            string_mapper: The function to map the raw search results to strings.
                When using this from a vector store, your results are of type
                VectorSearchResult[TModel],
                so the string_mapper can be used to extract the fields you want from the result.
                The default is to use the model_dump_json method of the result, which will return a json-like string.

        Returns:
            KernelFunction: The kernel function.
        """
        ...

    def create_search_function(
        self,
        function_name=DEFAULT_FUNCTION_NAME,
        description=DEFAULT_DESCRIPTION,
        *,
        output_type="str",
        parameters=None,
        return_parameter=None,
        filter=None,
        top=5,
        skip=0,
        include_total_count=False,
        filter_update_function=None,
        string_mapper=None,
    ) -> KernelFunction:
        """Create a kernel function from a search function."""
        options = SearchOptions(
            filter=filter,
            skip=skip,
            top=top,
            include_total_count=include_total_count,
        )
        match output_type:
            case "str":
                return self._create_kernel_function(
                    output_type=str,
                    options=options,
                    parameters=parameters,
                    filter_update_function=filter_update_function,
                    return_parameter=return_parameter,
                    function_name=function_name,
                    description=description,
                    string_mapper=string_mapper,
                )
            case "TextSearchResult":
                return self._create_kernel_function(
                    output_type=TextSearchResult,
                    options=options,
                    parameters=parameters,
                    filter_update_function=filter_update_function,
                    return_parameter=return_parameter,
                    function_name=function_name,
                    description=description,
                    string_mapper=string_mapper,
                )
            case "Any":
                return self._create_kernel_function(
                    output_type="Any",
                    options=options,
                    parameters=parameters,
                    filter_update_function=filter_update_function,
                    return_parameter=return_parameter,
                    function_name=function_name,
                    description=description,
                    string_mapper=string_mapper,
                )
            case _:
                raise TextSearchException(
                    f"Unknown output type: {output_type}. Must be 'str', 'TextSearchResult', or 'Any'."
                )

    # endregion
    # region: Private methods

    def _create_kernel_function(
        self,
        output_type: type[str] | type[TSearchResult] | Literal["Any"] = str,
        options: SearchOptions | None = None,
        parameters: list[KernelParameterMetadata] | None = None,
        filter_update_function: DynamicFilterFunction | None = None,
        return_parameter: KernelParameterMetadata | None = None,
        function_name: str = DEFAULT_FUNCTION_NAME,
        description: str = DEFAULT_DESCRIPTION,
        string_mapper: Callable[[TSearchResult], str] | None = None,
    ) -> KernelFunction:
        """Create a kernel function from a search function."""
        update_func = filter_update_function or default_dynamic_filter_function

        @kernel_function(name=function_name, description=description)
        async def search_wrapper(**kwargs: Any) -> Sequence[str]:
            query = kwargs.pop("query", "")
            try:
                inner_options = create_options(SearchOptions, deepcopy(options), **kwargs)
            except ValidationError:
                # this usually only happens when the kwargs are invalid, so blank options in this case.
                inner_options = SearchOptions()
            inner_options.filter = update_func(filter=inner_options.filter, parameters=parameters, **kwargs)
            try:
                results = await self.search(
                    query=query,
                    output_type=output_type,
                    **inner_options.model_dump(exclude_none=True, exclude_defaults=True, exclude_unset=True),
                )
            except Exception as e:
                msg = f"Exception in search function: {e}"
                logger.error(msg)
                raise TextSearchException(msg) from e
            return await self._map_results(results, string_mapper)

        return KernelFunctionFromMethod(
            method=search_wrapper,
            parameters=self._default_parameter_metadata() if parameters is None else parameters,
            return_parameter=return_parameter or self._default_return_parameter_metadata(),
        )

    async def _map_results(
        self,
        results: KernelSearchResults[TSearchResult],
        string_mapper: Callable[[TSearchResult], str] | None = None,
    ) -> list[str]:
        """Map search results to strings."""
        if string_mapper:
            return [string_mapper(result) async for result in results.results]
        return [self._default_map_to_string(result) async for result in results.results]

    @staticmethod
    def _default_map_to_string(result: BaseModel | object) -> str:
        """Default mapping function for text search results."""
        if isinstance(result, BaseModel):
            return result.model_dump_json()
        return result if isinstance(result, str) else json.dumps(result)

    # region: Abstract methods

    @abstractmethod
    async def search(
        self,
        query: str,
        output_type: type[str] | type[TSearchResult] | Literal["Any"] = str,
        **kwargs: Any,
    ) -> "KernelSearchResults[TSearchResult]":
        """Search for text, returning a KernelSearchResult with a list of strings.

        Args:
            query: The query to search for.
            output_type: The type of the output, default is str.
                Can also be TextSearchResult or Any.
            **kwargs: Additional keyword arguments to pass to the search function.

        """
        ...
