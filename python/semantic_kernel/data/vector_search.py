# Copyright (c) Microsoft. All rights reserved.

import json
import logging
from abc import abstractmethod
from ast import AST, Lambda, parse, walk
from collections.abc import AsyncIterable, Callable, Sequence
from enum import Enum
from inspect import getsource
from typing import Annotated, Any, ClassVar, Generic, TypeVar, overload

from pydantic import Field

from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.data.text_search import (
    KernelSearchResults,
    SearchOptions,
    TextSearch,
    TextSearchResult,
    create_options,
)
from semantic_kernel.data.vector_storage import TKey, TModel, VectorStoreRecordHandler
from semantic_kernel.exceptions import (
    VectorSearchExecutionException,
    VectorSearchOptionsException,
    VectorStoreModelDeserializationException,
)
from semantic_kernel.exceptions.vector_store_exceptions import (
    VectorStoreOperationException,
    VectorStoreOperationNotSupportedException,
)
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.kernel_types import OptionalOneOrMany
from semantic_kernel.utils.feature_stage_decorator import release_candidate
from semantic_kernel.utils.list_handler import desync_list

TSearchOptions = TypeVar("TSearchOptions", bound=SearchOptions)
logger = logging.getLogger(__name__)


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

    vector_field_name: str | None = None
    keyword_field_name: str | None = None
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
        options: SearchOptions | None = None,
        **kwargs: Any,
    ) -> KernelSearchResults[VectorSearchResult[TModel]]:
        """Search the vector store with Vector search for records that match the given value and filter.

        Args:
            values: The values to search for. These will be vectorized,
                either by the store or using the provided generator.
            options: The options to use for the search.
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
        options: SearchOptions | None = None,
        *,
        vector: Sequence[float | int],
        **kwargs: Any,
    ) -> KernelSearchResults[VectorSearchResult[TModel]]:
        """Search the vector store with Vector search for records that match the given vector and filter.

        Args:
            vector: The vector to search for
            options: The options to use for the search.
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
        options=None,
        *,
        vector=None,
        **kwargs,
    ):
        """Search the vector store for records that match the given value and filter.

        Args:
            values: The values to search for.
            vector: The vector to search for, if not provided, the values will be used to generate a vector.
            options: The options to use for the search.
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
        options = create_options(self.options_class, options, **kwargs)
        assert isinstance(options, VectorSearchOptions)  # nosec
        try:
            return await self._inner_search(
                search_type=SearchType.VECTOR,
                keywords=values,
                options=options,
                vector=vector,
                **kwargs,
            )
        except (
            VectorStoreModelDeserializationException,
            VectorSearchOptionsException,
            VectorSearchExecutionException,
            VectorStoreOperationNotSupportedException,
        ):
            raise  # pragma: no cover
        except Exception as exc:
            raise VectorSearchExecutionException(f"An error occurred during the search: {exc}") from exc

    async def hybrid_search(
        self,
        values: Any,
        options: SearchOptions | None = None,
        *,
        vector: list[float | int] | None = None,
        **kwargs: Any,
    ) -> KernelSearchResults[VectorSearchResult[TModel]]:
        """Search the vector store for records that match the given values and filter.

        Args:
            values: The values to search for.
            options: The options to use for the search.
            vector: The vector to search for, if not provided, the values will be used to generate a vector.
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
        options = create_options(self.options_class, options, **kwargs)
        assert isinstance(options, VectorSearchOptions)  # nosec
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
        if not values:
            return None
        vector_field = self.data_model_definition.try_get_vector_field(options.vector_field_name)
        if not vector_field:
            raise VectorSearchOptionsException(
                f"Vector field '{options.vector_field_name}' not found in data model definition."
            )
        embedding_generator = (
            vector_field.embedding_generator if vector_field.embedding_generator else self.embedding_generator
        )
        if not embedding_generator:
            raise VectorSearchOptionsException(
                f"Embedding generator not found for vector field '{options.vector_field_name}'."
            )

        return (
            await embedding_generator.generate_embeddings(
                # TODO (eavanvalkenburg): this only deals with string values, should support other types as well
                # but that requires work on the embedding generators first.
                texts=[values if isinstance(values, str) else json.dumps(values)],
                settings=PromptExecutionSettings(dimensions=vector_field.dimensions),
            )
        )[0].tolist()

    def as_text_search(
        self,
        search_type: str | SearchType = SearchType.VECTOR,
        string_mapper: Callable | None = None,
        text_search_results_mapper: Callable | None = None,
        **kwargs: Any,
    ) -> "VectorStoreTextSearch[TModel]":
        """Convert the vector search to a text search.

        Args:
            search_type: The type of search to perform.
            string_mapper: A function to map the string results.
            text_search_results_mapper: A function to map the text search results.
            **kwargs: Additional arguments that might be needed.
        """
        return VectorStoreTextSearch(
            vector_search=self,
            search_type=search_type if isinstance(search_type, SearchType) else SearchType(search_type),
            string_mapper=string_mapper,
            text_search_results_mapper=text_search_results_mapper,
            **kwargs,
        )

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
        if search_filter is None:
            return None

        filters = search_filter if isinstance(search_filter, list) else [search_filter]

        created_filters: list[Any] = []
        for filter_ in filters:
            # parse lambda expression with AST
            tree = parse(filter_ if isinstance(filter_, str) else getsource(filter_).strip())
            for node in walk(tree):
                if isinstance(node, Lambda):
                    created_filters.append(self._lambda_parser(node.body))
                    break
            else:
                raise VectorStoreOperationException("No lambda expression found in the filter.")
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


# region: VectorStoreTextSearch


class VectorStoreTextSearch(KernelBaseModel, TextSearch, Generic[TModel]):
    """Class that wraps a Vector Store Record Collection to expose it as a Text Search.

    Set the `search_type` to `SearchType.VECTOR` to use the vector search or
    `SearchType.KEYWORD_HYBRID` to use the hybrid search.

    The TextSearch class has three search methods:
    - `search`: Search for a query, returning a KernelSearchResult with a string as the results type.
    - `get_text_search_results`: Search for a query, returning a KernelSearchResult with a TextSearchResult as
        the results type.
    - `get_search_results`: Search for a query, returning a KernelSearchResult with a VectorSearchResult[TModel] as
        the results type.

    The `string_mapper` is used to map the record to a string for the `search` method.
    The `text_search_results_mapper` is used to map the record to a TextSearchResult for
        the `get_text_search_results` method.
    Or use `get_search_results` to get the raw results from the vector store.

    Args:
        vector_search: A search mixin to use for text search.
        search_type: The type of search to use. Defaults to `SearchType.VECTOR`.
        string_mapper: A function to map a record to a string.
        text_search_results_mapper: A function to map a record to a TextSearchResult.

    """

    vector_search: VectorSearch
    search_type: SearchType = SearchType.VECTOR
    string_mapper: Callable[[TModel], str] | None = None
    text_search_results_mapper: Callable[[TModel], TextSearchResult] | None = None

    async def search(
        self, query: str, options: "SearchOptions | None" = None, **kwargs: Any
    ) -> "KernelSearchResults[str]":
        """Search for a query, returning a KernelSearchResult with a string as the results type."""
        search_results = await self._execute_search(query, options, **kwargs)
        return KernelSearchResults(
            results=self._get_results_as_strings(search_results.results),
            total_count=search_results.total_count,
            metadata=search_results.metadata,
        )

    async def get_text_search_results(
        self, query: str, options: "SearchOptions | None" = None, **kwargs: Any
    ) -> "KernelSearchResults[TextSearchResult]":
        """Search for a query, returning a KernelSearchResult with a TextSearchResult as the results type."""
        search_results = await self._execute_search(query, options, **kwargs)
        return KernelSearchResults(
            results=self._get_results_as_text_search_result(search_results.results),
            total_count=search_results.total_count,
            metadata=search_results.metadata,
        )

    async def get_search_results(
        self, query: str, options: "SearchOptions | None" = None, **kwargs: Any
    ) -> "KernelSearchResults[VectorSearchResult[TModel]]":
        """Search for a query, returning a KernelSearchResult with a VectorSearchResult[TModel] as the results type."""
        return await self._execute_search(query, options, **kwargs)

    async def _execute_search(
        self, query: str, options: "SearchOptions | None", **kwargs: Any
    ) -> "KernelSearchResults[VectorSearchResult[TModel]]":
        """Internal method to execute the search."""
        if self.search_type == SearchType.VECTOR:
            return await self.vector_search.search(query, options=options, **kwargs)
        if self.search_type == SearchType.KEYWORD_HYBRID:
            return await self.vector_search.hybrid_search(values=query, options=options, **kwargs)
        raise VectorSearchExecutionException("No search method available.")  # pragma: no cover

    async def _get_results_as_strings(self, results: AsyncIterable[VectorSearchResult[TModel]]) -> AsyncIterable[str]:
        """Get the results as strings."""
        if self.string_mapper:
            async for result in results:
                if result.record:
                    yield self.string_mapper(result.record)
            return
        async for result in results:
            if result.record:
                yield self._default_map_to_string(result.record)

    async def _get_results_as_text_search_result(
        self, results: AsyncIterable[VectorSearchResult[TModel]]
    ) -> AsyncIterable[TextSearchResult]:
        """Get the results as strings."""
        if self.text_search_results_mapper:
            async for result in results:
                if result.record:
                    yield self.text_search_results_mapper(result.record)
            return
        async for result in results:
            if result.record:
                yield TextSearchResult(value=self._default_map_to_string(result.record))

    @property
    def options_class(self) -> type["SearchOptions"]:
        """Get the options class."""
        return VectorSearchOptions
