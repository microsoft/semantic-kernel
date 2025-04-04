# Copyright (c) Microsoft. All rights reserved.

import json
import logging
import sys
from abc import ABC, abstractmethod
from collections.abc import AsyncIterable, Callable, Mapping, Sequence
from copy import deepcopy
from typing import Annotated, Any, ClassVar, Generic, Protocol, TypeVar

from pydantic import BaseModel, Field, ValidationError

from semantic_kernel.data.const import DEFAULT_DESCRIPTION, DEFAULT_FUNCTION_NAME, TextSearchFunctions
from semantic_kernel.exceptions import TextSearchException
from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.functions.kernel_function_from_method import KernelFunctionFromMethod
from semantic_kernel.functions.kernel_parameter_metadata import KernelParameterMetadata
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.utils.feature_stage_decorator import experimental

if sys.version_info >= (3, 11):
    from typing import Self  # pragma: no cover
else:
    from typing_extensions import Self  # pragma: no cover

TSearchResult = TypeVar("TSearchResult")
TSearchFilter = TypeVar("TSearchFilter", bound="SearchFilter")
TMapInput = TypeVar("TMapInput")

logger = logging.getLogger(__name__)

# region: Filters


@experimental
class FilterClauseBase(ABC, KernelBaseModel):
    """A base for all filter clauses."""

    filter_clause_type: ClassVar[str] = "FilterClauseBase"
    field_name: str
    value: Any

    def __str__(self) -> str:
        """Return a string representation of the filter clause."""
        return f"filter_clause_type='{self.filter_clause_type}' field_name='{self.field_name}' value='{self.value}'"


@experimental
class AnyTagsEqualTo(FilterClauseBase):
    """A filter clause for a any tags equals comparison.

    Args:
        field_name: The name of the field containing the list of tags.
        value: The value to compare against the list of tags.
    """

    filter_clause_type: ClassVar[str] = "any_tags_equal_to"


@experimental
class EqualTo(FilterClauseBase):
    """A filter clause for an equals comparison.

    Args:
        field_name: The name of the field to compare.
        value: The value to compare against the field.

    """

    filter_clause_type: ClassVar[str] = "equal_to"


@experimental
class SearchFilter:
    """A filter clause for a search."""

    def __init__(self) -> None:
        """Initialize a new instance of SearchFilter."""
        self.filters: list[FilterClauseBase] = []
        self.group_type = "AND"
        self.equal_to = self.__equal_to

    def __equal_to(self, field_name: str, value: str) -> Self:
        """Add an equals filter clause."""
        self.filters.append(EqualTo(field_name=field_name, value=value))
        return self

    @classmethod
    def equal_to(cls: type[TSearchFilter], field_name: str, value: str) -> TSearchFilter:
        """Add an equals filter clause."""
        filter = cls()
        filter.equal_to(field_name, value)
        return filter

    def __str__(self) -> str:
        """Return a string representation of the filter."""
        return f"{f' {self.group_type} '.join(f'({f!s})' for f in self.filters)}"


# region: Options


@experimental
class SearchOptions(ABC, KernelBaseModel):
    """Options for a search."""

    filter: SearchFilter = Field(default_factory=SearchFilter)
    include_total_count: bool = False


@experimental
class TextSearchOptions(SearchOptions):
    """Options for a text search."""

    top: Annotated[int, Field(gt=0)] = 5
    skip: Annotated[int, Field(ge=0)] = 0


# region: Results


@experimental
class KernelSearchResults(KernelBaseModel, Generic[TSearchResult]):
    """The result of a kernel search."""

    results: AsyncIterable[TSearchResult]
    total_count: int | None = None
    metadata: Mapping[str, Any] | None = None


@experimental
class TextSearchResult(KernelBaseModel):
    """The result of a text search."""

    name: str | None = None
    value: str | None = None
    link: str | None = None


# region: Options functions


class OptionsUpdateFunctionType(Protocol):
    """Type definition for the options update function in Text Search."""

    def __call__(
        self,
        query: str,
        options: "SearchOptions",
        parameters: list["KernelParameterMetadata"] | None = None,
        **kwargs: Any,
    ) -> tuple[str, "SearchOptions"]:
        """Signature of the function."""
        ...  # pragma: no cover


def create_options(
    options_class: type["SearchOptions"],
    options: "SearchOptions | None",
    **kwargs: Any,
) -> "SearchOptions":
    """Create search options.

    If options are supplied, they are checked for the right type, and the kwargs are used to update the options.

    If options are not supplied, they are created from the kwargs.
    If that fails, an empty options object is returned.

    Args:
        options_class: The class of the options.
        options: The existing options to update.
        **kwargs: The keyword arguments to use to create the options.

    Returns:
        SearchOptions: The options.

    Raises:
        ValidationError: If the options are not valid.

    """
    # no options give, so just try to create from kwargs
    if not options:
        return options_class.model_validate(kwargs)
    # options are the right class, just update based on kwargs
    if isinstance(options, options_class):
        for key, value in kwargs.items():
            if key in options.model_fields:
                setattr(options, key, value)
        return options
    # options are not the right class, so create new options
    # first try to dump the existing, if this doesn't work for some reason, try with kwargs only
    inputs = {}
    try:
        inputs = options.model_dump(exclude_none=True, exclude_defaults=True, exclude_unset=True)
    except Exception:
        # This is very unlikely to happen, but if it does, we will just create new options.
        # one reason this could happen is if a different class is passed that has no model_dump method
        logger.warning("Options are not valid. Creating new options from just kwargs.")
    inputs.update(kwargs)
    return options_class.model_validate(kwargs)


def default_options_update_function(
    query: str, options: "SearchOptions", parameters: list["KernelParameterMetadata"] | None = None, **kwargs: Any
) -> tuple[str, "SearchOptions"]:
    """The default options update function.

    This function is used to update the query and options with the kwargs.
    You can supply your own version of this function to customize the behavior.

    Args:
        query: The query.
        options: The options.
        parameters: The parameters to use to create the options.
        **kwargs: The keyword arguments to use to update the options.

    Returns:
        tuple[str, SearchOptions]: The updated query and options

    """
    for param in parameters or []:
        assert param.name  # nosec, when used param name is always set
        if param.name in {"query", "top", "skip"}:
            continue
        if param.name in kwargs:
            options.filter.equal_to(param.name, kwargs[param.name])
        if param.default_value:
            options.filter.equal_to(param.name, param.default_value)

    return query, options


# region: Text Search


@experimental
class TextSearch:
    """The base class for all text searches."""

    @property
    def options_class(self) -> type["SearchOptions"]:
        """The options class for the search."""
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

    def create_search(
        self,
        options: SearchOptions | None = None,
        parameters: list[KernelParameterMetadata] | None = None,
        options_update_function: OptionsUpdateFunctionType | None = None,
        return_parameter: KernelParameterMetadata | None = None,
        function_name: str = DEFAULT_FUNCTION_NAME,
        description: str = DEFAULT_DESCRIPTION,
        string_mapper: Callable[[TMapInput], str] | None = None,
    ) -> KernelFunction:
        """Create a kernel function from a search function.

        Args:
            options: The search options.
            parameters: The parameters for the function, a list of KernelParameterMetadata.
            options_update_function: A function to update the search options.
                The function should return the updated query and options.
                There is a default function that can be used, or you can supply your own.
                The default function uses the parameters and the kwargs to update the options.
                Adding equal to filters to the options for all parameters that are not "query", "top", or "skip".
                As well as adding equal to filters for parameters that have a default value.
            return_parameter: The return parameter for the function.
            function_name: The name of the function, to be used in the kernel, default is "search".
            description: The description of the function, a default is provided.
            string_mapper: The function to map the search results to strings.

        Returns:
            KernelFunction: The kernel function.

        """
        return self._create_kernel_function(
            search_function=TextSearchFunctions.SEARCH,
            options=options,
            parameters=parameters,
            options_update_function=options_update_function,
            return_parameter=return_parameter,
            function_name=function_name,
            description=description,
            string_mapper=string_mapper,
        )

    def create_get_text_search_results(
        self,
        options: SearchOptions | None = None,
        parameters: list[KernelParameterMetadata] | None = None,
        options_update_function: OptionsUpdateFunctionType | None = None,
        return_parameter: KernelParameterMetadata | None = None,
        function_name: str = DEFAULT_FUNCTION_NAME,
        description: str = DEFAULT_DESCRIPTION,
        string_mapper: Callable[[TMapInput], str] | None = None,
    ) -> KernelFunction:
        """Create a kernel function from a get_text_search_results function.

        Args:
            options: The search options.
            parameters: The parameters for the function, a list of KernelParameterMetadata.
            options_update_function: A function to update the search options.
                The function should return the updated query and options.
                There is a default function that can be used, or you can supply your own.
                The default function uses the parameters and the kwargs to update the options.
                Adding equal to filters to the options for all parameters that are not "query", "top", or "skip".
                As well as adding equal to filters for parameters that have a default value.
            return_parameter: The return parameter for the function.
            function_name: The name of the function, to be used in the kernel, default is "search".
            description: The description of the function, a default is provided.
            string_mapper: The function to map the search results to strings.

        Returns:
            KernelFunction: The kernel function.
        """
        return self._create_kernel_function(
            search_function=TextSearchFunctions.GET_TEXT_SEARCH_RESULT,
            options=options,
            parameters=parameters,
            options_update_function=options_update_function,
            return_parameter=return_parameter,
            function_name=function_name,
            description=description,
            string_mapper=string_mapper,
        )

    def create_get_search_results(
        self,
        options: SearchOptions | None = None,
        parameters: list[KernelParameterMetadata] | None = None,
        options_update_function: OptionsUpdateFunctionType | None = None,
        return_parameter: KernelParameterMetadata | None = None,
        function_name: str = DEFAULT_FUNCTION_NAME,
        description: str = DEFAULT_DESCRIPTION,
        string_mapper: Callable[[TMapInput], str] | None = None,
    ) -> KernelFunction:
        """Create a kernel function from a get_search_results function.

        Args:
            options: The search options.
            parameters: The parameters for the function, a list of KernelParameterMetadata.
            options_update_function: A function to update the search options.
                The function should return the updated query and options.
                There is a default function that can be used, or you can supply your own.
                The default function uses the parameters and the kwargs to update the options.
                Adding equal to filters to the options for all parameters that are not "query", "top", or "skip".
                As well as adding equal to filters for parameters that have a default value.
            return_parameter: The return parameter for the function.
            function_name: The name of the function, to be used in the kernel, default is "search".
            description: The description of the function, a default is provided.
            string_mapper: The function to map the search results to strings.

        Returns:
            KernelFunction: The kernel function.
        """
        return self._create_kernel_function(
            search_function=TextSearchFunctions.GET_SEARCH_RESULT,
            options=options,
            parameters=parameters,
            options_update_function=options_update_function,
            return_parameter=return_parameter,
            function_name=function_name,
            description=description,
            string_mapper=string_mapper,
        )

    # endregion
    # region: Private methods

    def _create_kernel_function(
        self,
        search_function: TextSearchFunctions | str = TextSearchFunctions.SEARCH,
        options: SearchOptions | None = None,
        parameters: list[KernelParameterMetadata] | None = None,
        options_update_function: OptionsUpdateFunctionType | None = None,
        return_parameter: KernelParameterMetadata | None = None,
        function_name: str = DEFAULT_FUNCTION_NAME,
        description: str = DEFAULT_DESCRIPTION,
        string_mapper: Callable[[TMapInput], str] | None = None,
    ) -> KernelFunction:
        """Create a kernel function from a search function.

        Args:
            search_function: The search function,
                options are "search", "get_text_search_result", and "get_search_result".
                Default is "search".
            options: The search options.
            parameters: The parameters for the function,
                use an empty list for a function without parameters,
                use None for the default set, which is "query", "top", and "skip".
            options_update_function: A function to update the search options.
                The function should return the updated query and options.
                There is a default function that can be used, or you can supply your own.
                The default function uses the parameters and the kwargs to update the options.
                Adding equal to filters to the options for all parameters that are not "query", "top", or "skip".
                As well as adding equal to filters for parameters that have a default value.
            return_parameter: The return parameter for the function.
            function_name: The name of the function, to be used in the kernel, default is "search".
            description: The description of the function, a default is provided.
            string_mapper: The function to map the search results to strings.
                This can be applied to the results from the chosen search function.
                When using the VectorStoreTextSearch and the Search method, a
                string_mapper can be defined there as well, that is separate from this one.
                The default serializes the result as json strings.

        Returns:
            KernelFunction: The kernel function.

        """
        if isinstance(search_function, str):
            search_function = TextSearchFunctions(search_function)

        update_func = options_update_function or default_options_update_function

        @kernel_function(name=function_name, description=description)
        async def search_wrapper(**kwargs: Any) -> Sequence[str]:
            query = kwargs.pop("query", "")
            try:
                inner_options = create_options(self.options_class, deepcopy(options), **kwargs)
            except ValidationError:
                # this usually only happens when the kwargs are invalid, so blank options in this case.
                inner_options = self.options_class()
            query, inner_options = update_func(query=query, options=inner_options, parameters=parameters, **kwargs)
            try:
                results = await self._get_search_function(search_function)(
                    query=query,
                    options=inner_options,
                )
            except Exception as e:
                msg = f"Exception in search function ({search_function.value}): {e}"
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
        results: KernelSearchResults[TMapInput],
        string_mapper: Callable[[TMapInput], str] | None = None,
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

    def _get_search_function(self, search_function: TextSearchFunctions) -> Callable:
        """Get the search function."""
        match search_function:
            case TextSearchFunctions.SEARCH:
                return self.search
            case TextSearchFunctions.GET_TEXT_SEARCH_RESULT:
                return self.get_text_search_results
            case TextSearchFunctions.GET_SEARCH_RESULT:
                return self.get_search_results
        raise TextSearchException(f"Unknown search function: {search_function}")  # pragma: no cover

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
    async def get_text_search_results(
        self,
        query: str,
        options: "SearchOptions | None" = None,
        **kwargs: Any,
    ) -> "KernelSearchResults[TextSearchResult]":
        """Search for text, returning a KernelSearchResult with TextSearchResults."""
        ...

    @abstractmethod
    async def get_search_results(
        self,
        query: str,
        options: "SearchOptions | None" = None,
        **kwargs: Any,
    ) -> "KernelSearchResults[Any]":
        """Search for text, returning a KernelSearchResult with the results directly from the service."""
        ...
