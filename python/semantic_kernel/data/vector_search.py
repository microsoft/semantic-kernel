# Copyright (c) Microsoft. All rights reserved.

import json
import logging
from abc import abstractmethod
from ast import AST, Lambda, NodeVisitor, expr, parse
from collections.abc import AsyncIterable, Callable, Sequence
from copy import deepcopy
from enum import Enum
from inspect import getsource
from typing import Annotated, Any, ClassVar, Generic, Literal, TypeVar, overload

from pydantic import Field, ValidationError

from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.data.const import DEFAULT_DESCRIPTION, DEFAULT_FUNCTION_NAME
from semantic_kernel.data.text_search import (
    DynamicFilterFunction,
    KernelSearchResults,
    SearchOptions,
    TextSearch,
    create_options,
    default_dynamic_filter_function,
)
from semantic_kernel.data.vector_storage import TKey, TModel, VectorStoreRecordHandler
from semantic_kernel.exceptions import (
    VectorSearchExecutionException,
    VectorSearchOptionsException,
    VectorStoreModelDeserializationException,
)
from semantic_kernel.exceptions.search_exceptions import TextSearchException
from semantic_kernel.exceptions.vector_store_exceptions import (
    VectorStoreOperationException,
    VectorStoreOperationNotSupportedException,
)
from semantic_kernel.functions import kernel_function
from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.functions.kernel_function_from_method import KernelFunctionFromMethod
from semantic_kernel.functions.kernel_parameter_metadata import KernelParameterMetadata
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.kernel_types import OptionalOneOrList, OptionalOneOrMany
from semantic_kernel.utils.feature_stage_decorator import release_candidate
from semantic_kernel.utils.list_handler import desync_list

TSearchOptions = TypeVar("TSearchOptions", bound=SearchOptions)
logger = logging.getLogger(__name__)


TFilters = TypeVar("TFilters")


class LambdaVisitor(NodeVisitor, Generic[TFilters]):
    """Visitor class to visit the AST nodes."""

    def __init__(self, lambda_parser: Callable[[expr], TFilters], output_filters: list[TFilters] | None = None) -> None:
        """Initialize the visitor with a lambda parser and output filters."""
        self.lambda_parser = lambda_parser
        self.output_filters = output_filters if output_filters is not None else []

    def visit_Lambda(self, node: Lambda) -> None:
        """This method is called when a lambda expression is found."""
        self.output_filters.append(self.lambda_parser(node.body))


# region: Search Type


@release_candidate
class SearchType(str, Enum):
    """Enumeration for search types.

    Contains: vector and keyword_hybrid.
    """

    VECTOR = "vector"
    KEYWORD_HYBRID = "keyword_hybrid"


# region: Options


@release_candidate
class VectorSearchOptions(SearchOptions):
    """Options for vector search, builds on TextSearchOptions.

    When multiple filters are used, they are combined with an AND operator.
    """

    vector_property_name: str | None = None
    additional_property_name: str | None = None
    top: Annotated[int, Field(gt=0)] = 3
    include_vectors: bool = False


# region: Results


@release_candidate
class VectorSearchResult(KernelBaseModel, Generic[TModel]):
    """The result of a vector search."""

    record: TModel
    score: float | None = None


# region: Vector Search


@release_candidate
class VectorSearch(VectorStoreRecordHandler[TKey, TModel], Generic[TKey, TModel]):
    """Base class for searching vectors."""

    supported_search_types: ClassVar[set[SearchType]] = Field(default_factory=set)

    @property
    def options_class(self) -> type[SearchOptions]:
        """The options class for the search."""
        return VectorSearchOptions

    # region: Abstract methods to be implemented by vector stores

    @abstractmethod
    async def _inner_search(
        self,
        search_type: SearchType,
        options: VectorSearchOptions,
        values: Any | None = None,
        vector: Sequence[float | int] | None = None,
        **kwargs: Any,
    ) -> KernelSearchResults[VectorSearchResult[TModel]]:
        """Inner search method.

        This is the main search method that should be implemented, and will be called by the public search methods.
        Currently, at least one of the three search contents will be provided
        (through the public interface mixin functions), in the future, this may be expanded to allow multiple of them.

        This method should return a KernelSearchResults object with the results of the search.
        The inner "results" object of the KernelSearchResults should be a async iterator that yields the search results,
        this allows things like paging to be implemented.

        There is a default helper method "_get_vector_search_results_from_results" to convert
        the results to a async iterable VectorSearchResults, but this can be overridden if necessary.

        Options might be a object of type VectorSearchOptions, or a subclass of it.

        The implementation of this method must deal with the possibility that multiple search contents are provided,
        and should handle them in a way that makes sense for that particular store.

        The public methods will catch and reraise the three exceptions mentioned below, others are caught and turned
        into a VectorSearchExecutionException.

        Args:
            search_type: The type of search to perform.
            options: The search options, can be None.
            values: The values to search for, optional.
            vector: The vector to search for, optional.
            **kwargs: Additional arguments that might be needed.

        Returns:
            The search results, wrapped in a KernelSearchResults object.

        Raises:
            VectorSearchExecutionException: If an error occurs during the search.
            VectorStoreModelDeserializationException: If an error occurs during deserialization.
            VectorSearchOptionsException: If the search options are invalid.
            VectorStoreOperationNotSupportedException: If the search type is not supported.

        """
        ...

    @abstractmethod
    def _get_record_from_result(self, result: Any) -> Any:
        """Get the record from the returned search result.

        Does any unpacking or processing of the result to get just the record.

        If the underlying SDK of the store returns a particular type that might include something
        like a score or other metadata, this method should be overridden to extract just the record.

        Likely returns a dict, but in some cases could return the record in the form of a SDK specific object.

        This method is used as part of the _get_vector_search_results_from_results method,
        the output of it is passed to the deserializer.
        """
        ...

    @abstractmethod
    def _get_score_from_result(self, result: Any) -> float | None:
        """Get the score from the result.

        Does any unpacking or processing of the result to get just the score.

        If the underlying SDK of the store returns a particular type with a score or other metadata,
        this method extracts it.
        """
        ...

    # region: New methods

    async def _get_vector_search_results_from_results(
        self, results: AsyncIterable[Any] | Sequence[Any], options: VectorSearchOptions | None = None
    ) -> AsyncIterable[VectorSearchResult[TModel]]:
        if isinstance(results, Sequence):
            results = desync_list(results)
        async for result in results:
            if not result:
                continue
            try:
                record = self.deserialize(
                    self._get_record_from_result(result), include_vectors=options.include_vectors if options else True
                )
            except VectorStoreModelDeserializationException:
                raise
            except Exception as exc:
                raise VectorStoreModelDeserializationException(
                    f"An error occurred while deserializing the record: {exc}"
                ) from exc
            score = self._get_score_from_result(result)
            if record is not None:
                # single records are always returned as single records by the deserializer
                yield VectorSearchResult(record=record, score=score)  # type: ignore

    @overload
    async def search(
        self,
        values: Any,
        *,
        vector_field_name: str | None = None,
        filter: OptionalOneOrList[Callable | str] = None,
        top: int = 3,
        skip: int = 0,
        include_total_count: bool = False,
        include_vectors: bool = False,
        **kwargs: Any,
    ) -> KernelSearchResults[VectorSearchResult[TModel]]:
        """Search the vector store with Vector search for records that match the given value and filter.

        Args:
            values: The values to search for. These will be vectorized,
                either by the store or using the provided generator.
            vector_field_name: The name of the vector field to use for the search.
            filter: The filter to apply to the search.
            top: The number of results to return.
            skip: The number of results to skip.
            include_total_count: Whether to include the total count of results.
            include_vectors: Whether to include the vectors in the results.
            kwargs: If options are not set, this is used to create them.
                they are passed on to the inner search method.

        Raises:
            VectorSearchExecutionException: If an error occurs during the search.
            VectorStoreModelDeserializationException: If an error occurs during deserialization.
            VectorSearchOptionsException: If the search options are invalid.
            VectorStoreOperationNotSupportedException: If the search type is not supported.

        """
        ...

    @overload
    async def search(
        self,
        *,
        vector: Sequence[float | int],
        vector_field_name: str | None = None,
        filter: OptionalOneOrList[Callable | str] = None,
        top: int = 3,
        skip: int = 0,
        include_total_count: bool = False,
        include_vectors: bool = False,
        **kwargs: Any,
    ) -> KernelSearchResults[VectorSearchResult[TModel]]:
        """Search the vector store with Vector search for records that match the given vector and filter.

        Args:
            vector: The vector to search for
            vector_field_name: The name of the vector field to use for the search.
            filter: The filter to apply to the search.
            top: The number of results to return.
            skip: The number of results to skip.
            include_total_count: Whether to include the total count of results.
            include_vectors: Whether to include the vectors in the results.
            kwargs: If options are not set, this is used to create them.
                they are passed on to the inner search method.

        Raises:
            VectorSearchExecutionException: If an error occurs during the search.
            VectorStoreModelDeserializationException: If an error occurs during deserialization.
            VectorSearchOptionsException: If the search options are invalid.
            VectorStoreOperationNotSupportedException: If the search type is not supported.

        """
        ...

    async def search(
        self,
        values=None,
        *,
        vector=None,
        vector_property_name=None,
        filter=None,
        top=3,
        skip=0,
        include_total_count=False,
        include_vectors=False,
        **kwargs,
    ):
        """Search the vector store for records that match the given value and filter.

        Args:
            values: The values to search for.
            vector: The vector to search for, if not provided, the values will be used to generate a vector.
            vector_property_name: The name of the vector property to use for the search.
            filter: The filter to apply to the search.
            top: The number of results to return.
            skip: The number of results to skip.
            include_total_count: Whether to include the total count of results.
            include_vectors: Whether to include the vectors in the results.
            kwargs: If options are not set, this is used to create them.
                they are passed on to the inner search method.

        Raises:
            VectorSearchExecutionException: If an error occurs during the search.
            VectorStoreModelDeserializationException: If an error occurs during deserialization.
            VectorSearchOptionsException: If the search options are invalid.
            VectorStoreOperationNotSupportedException: If the search type is not supported.

        """
        if SearchType.VECTOR not in self.supported_search_types:
            raise VectorStoreOperationNotSupportedException(
                f"Vector search is not supported by this vector store: {self.__class__.__name__}"
            )
        options = VectorSearchOptions(
            filter=filter,
            vector_property_name=vector_property_name,
            top=top,
            skip=skip,
            include_total_count=include_total_count,
            include_vectors=include_vectors,
        )
        try:
            return await self._inner_search(
                search_type=SearchType.VECTOR,
                values=values,
                options=options,
                vector=vector,
                **kwargs,
            )
        except (
            VectorStoreModelDeserializationException,
            VectorSearchOptionsException,
            VectorSearchExecutionException,
            VectorStoreOperationNotSupportedException,
            VectorStoreOperationException,
        ):
            raise  # pragma: no cover
        except Exception as exc:
            raise VectorSearchExecutionException(f"An error occurred during the search: {exc}") from exc

    async def hybrid_search(
        self,
        values: Any,
        *,
        vector: list[float | int] | None = None,
        vector_property_name: str | None = None,
        additional_property_name: str | None = None,
        filter: OptionalOneOrList[Callable | str] = None,
        top: int = 3,
        skip: int = 0,
        include_total_count: bool = False,
        include_vectors: bool = False,
        **kwargs: Any,
    ) -> KernelSearchResults[VectorSearchResult[TModel]]:
        """Search the vector store for records that match the given values and filter.

        Args:
            values: The values to search for.
            vector: The vector to search for, if not provided, the values will be used to generate a vector.
            vector_property_name: The name of the vector field to use for the search.
            additional_property_name: The name of the additional property field to use for the search.
            filter: The filter to apply to the search.
            top: The number of results to return.
            skip: The number of results to skip.
            include_total_count: Whether to include the total count of results.
            include_vectors: Whether to include the vectors in the results.
            kwargs: If options are not set, this is used to create them.
                they are passed on to the inner search method.

        Raises:
            VectorSearchExecutionException: If an error occurs during the search.
            VectorStoreModelDeserializationException: If an error occurs during deserialization.
            VectorSearchOptionsException: If the search options are invalid.
            VectorStoreOperationNotSupportedException: If the search type is not supported.

        """
        if SearchType.KEYWORD_HYBRID not in self.supported_search_types:
            raise VectorStoreOperationNotSupportedException(
                f"Keyword hybrid search is not supported by this vector store: {self.__class__.__name__}"
            )
        options = VectorSearchOptions(
            filter=filter,
            vector_property_name=vector_property_name,
            additional_property_name=additional_property_name,
            top=top,
            skip=skip,
            include_total_count=include_total_count,
            include_vectors=include_vectors,
        )
        try:
            return await self._inner_search(
                search_type=SearchType.KEYWORD_HYBRID,
                values=values,
                vector=vector,
                options=options,
                **kwargs,
            )
        except (
            VectorStoreModelDeserializationException,
            VectorSearchOptionsException,
            VectorSearchExecutionException,
            VectorStoreOperationNotSupportedException,
            VectorStoreOperationException,
        ):
            raise  # pragma: no cover
        except Exception as exc:
            raise VectorSearchExecutionException(f"An error occurred during the search: {exc}") from exc

    async def _generate_vector_from_values(
        self,
        values: Any | None,
        options: VectorSearchOptions,
    ) -> Sequence[float | int] | None:
        """Generate a vector from the given keywords."""
        if values is None:
            return None
        vector_field = self.data_model_definition.try_get_vector_field(options.vector_property_name)
        if not vector_field:
            raise VectorSearchOptionsException(
                f"Vector field '{options.vector_property_name}' not found in data model definition."
            )
        embedding_generator = (
            vector_field.embedding_generator if vector_field.embedding_generator else self.embedding_generator
        )
        if not embedding_generator:
            raise VectorSearchOptionsException(
                f"Embedding generator not found for vector field '{options.vector_property_name}'."
            )

        return (
            await embedding_generator.generate_embeddings(
                # TODO (eavanvalkenburg): this only deals with string values, should support other types as well
                # but that requires work on the embedding generators first.
                texts=[values if isinstance(values, str) else json.dumps(values)],
                settings=PromptExecutionSettings(dimensions=vector_field.dimensions),
            )
        )[0].tolist()

    def _build_filter(self, search_filter: OptionalOneOrMany[Callable | str] | None) -> OptionalOneOrMany[Any]:
        """Create the filter based on the filters.

        This function returns None, a single filter, or a list of filters.
        If a single filter is passed, a single filter is returned.

        It takes the filters, which can be a Callable (lambda) or a string, and parses them into a filter object,
        using the _lambda_parser method that is specific to each vector store.

        If a list of filters, is passed, the parsed filters are also returned as a list, so the caller needs to
        combine them in the appropriate way.

        Often called like this (when filters are strings):
        ```python
        if filter := self._build_filter(options.filter):
            search_args["filter"] = filter if isinstance(filter, str) else " and ".join(filter)
        ```
        """
        if not search_filter:
            return None

        filters = search_filter if isinstance(search_filter, list) else [search_filter]

        created_filters: list[Any] = []

        visitor = LambdaVisitor(self._lambda_parser)
        for filter_ in filters:
            # parse lambda expression with AST
            tree = parse(filter_ if isinstance(filter_, str) else getsource(filter_).strip())
            visitor.visit(tree)
        created_filters = visitor.output_filters
        if len(created_filters) == 0:
            raise VectorStoreOperationException("No filter strings found.")
        if len(created_filters) == 1:
            return created_filters[0]
        return created_filters

    @abstractmethod
    def _lambda_parser(self, node: AST) -> Any:
        """Parse the lambda expression and return the filter string.

        This follows from the ast specs: https://docs.python.org/3/library/ast.html
        """
        # This method should be implemented in the derived class
        # to parse the lambda expression and return the filter string.
        pass

    # region: Kernel Functions

    def create_search_function(
        self,
        function_name: str = DEFAULT_FUNCTION_NAME,
        description: str = DEFAULT_DESCRIPTION,
        *,
        search_type: Literal["vector", "keyword_hybrid"] = "vector",
        parameters: list[KernelParameterMetadata] | None = None,
        return_parameter: KernelParameterMetadata | None = None,
        filter: OptionalOneOrList[Callable | str] = None,
        top: int = 5,
        skip: int = 0,
        vector_property_name: str | None = None,
        additional_property_name: str | None = None,
        include_vectors: bool = False,
        include_total_count: bool = False,
        filter_update_function: DynamicFilterFunction | None = None,
        string_mapper: Callable[[VectorSearchResult[TModel]], str] | None = None,
    ) -> KernelFunction:
        """Create a kernel function from a search function.

        Args:
            function_name: The name of the function, to be used in the kernel, default is "search".
            description: The description of the function, a default is provided.
            search_type: The type of search to perform, can be 'vector' or 'keyword_hybrid'.
            parameters: The parameters for the function,
                use an empty list for a function without parameters,
                use None for the default set, which is "query", "top", and "skip".
            return_parameter: The return parameter for the function.
            filter: The filter to apply to the search.
            top: The number of results to return.
            skip: The number of results to skip.
            vector_property_name: The name of the vector property to use for the search.
            additional_property_name: The name of the additional property field to use for the search.
            include_vectors: Whether to include the vectors in the results.
            include_total_count: Whether to include the total count of results.
            filter_update_function: A function to update the filters.
                The function should return the updated filter.
                The default function uses the parameters and the kwargs to update the filters, it
                adds equal to filters to the options for all parameters that are not "query".
                As well as adding equal to filters for parameters that have a default value.
            string_mapper: The function to map the search results to strings.
        """
        search_types = SearchType(search_type)
        if search_types not in self.supported_search_types:
            raise VectorStoreOperationNotSupportedException(
                f"Search type '{search_types.value}' is not supported by this vector store: {self.__class__.__name__}"
            )
        options = VectorSearchOptions(
            filter=filter,
            skip=skip,
            top=top,
            include_total_count=include_total_count,
            include_vectors=include_vectors,
            vector_property_name=vector_property_name,
            additional_property_name=additional_property_name,
        )
        return self._create_kernel_function(
            search_type=search_types,
            options=options,
            parameters=parameters,
            filter_update_function=filter_update_function,
            return_parameter=return_parameter,
            function_name=function_name,
            description=description,
            string_mapper=string_mapper,
        )

    def _create_kernel_function(
        self,
        search_type: SearchType,
        options: SearchOptions | None = None,
        parameters: list[KernelParameterMetadata] | None = None,
        filter_update_function: DynamicFilterFunction | None = None,
        return_parameter: KernelParameterMetadata | None = None,
        function_name: str = DEFAULT_FUNCTION_NAME,
        description: str = DEFAULT_DESCRIPTION,
        string_mapper: Callable[[VectorSearchResult[TModel]], str] | None = None,
    ) -> KernelFunction:
        """Create a kernel function from a search function."""
        update_func = filter_update_function or default_dynamic_filter_function

        @kernel_function(name=function_name, description=description)
        async def search_wrapper(**kwargs: Any) -> Sequence[str]:
            query = kwargs.pop("query", "")
            try:
                inner_options = create_options(self.options_class, deepcopy(options), **kwargs)
            except ValidationError:
                # this usually only happens when the kwargs are invalid, so blank options in this case.
                inner_options = self.options_class()
            inner_options.filter = update_func(filter=inner_options.filter, parameters=parameters, **kwargs)
            match search_type:
                case SearchType.VECTOR:
                    try:
                        results = await self.search(
                            values=query,
                            **inner_options.model_dump(exclude_defaults=True, exclude_none=True),
                        )
                    except Exception as e:
                        msg = f"Exception in search function: {e}"
                        logger.error(msg)
                        raise TextSearchException(msg) from e
                case SearchType.KEYWORD_HYBRID:
                    try:
                        results = await self.hybrid_search(
                            values=query,
                            **inner_options.model_dump(exclude_defaults=True, exclude_none=True),
                        )
                    except Exception as e:
                        msg = f"Exception in hybrid search function: {e}"
                        logger.error(msg)
                        raise TextSearchException(msg) from e
                case _:
                    raise VectorStoreOperationNotSupportedException(
                        f"Search type '{search_type}' is not supported by this vector store: {self.__class__.__name__}"
                    )
            if string_mapper:
                return [string_mapper(result) async for result in results.results]
            return [result.model_dump_json(exclude_none=True) async for result in results.results]

        return KernelFunctionFromMethod(
            method=search_wrapper,
            parameters=TextSearch._default_parameter_metadata() if parameters is None else parameters,
            return_parameter=return_parameter or TextSearch._default_return_parameter_metadata(),
        )
