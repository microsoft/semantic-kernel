# Copyright (c) Microsoft. All rights reserved.

from collections.abc import AsyncIterable, Callable
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from pydantic import model_validator

from semantic_kernel.connectors.ai.embedding_generator_base import EmbeddingGeneratorBase
from semantic_kernel.data.text_search import KernelSearchResults, TextSearch, TextSearchResult
from semantic_kernel.data.vector_search import (
    VectorizableTextSearchMixin,
    VectorizedSearchMixin,
    VectorSearchOptions,
    VectorSearchResult,
    VectorTextSearchMixin,
)
from semantic_kernel.data.vector_storage import TModel
from semantic_kernel.exceptions import VectorSearchExecutionException, VectorStoreInitializationException
from semantic_kernel.kernel_pydantic import KernelBaseModel

if TYPE_CHECKING:
    from semantic_kernel.data.text_search import SearchOptions

_T = TypeVar("_T", bound="VectorStoreTextSearch")


class VectorStoreTextSearch(KernelBaseModel, TextSearch, Generic[TModel]):
    """Class that wraps a Vector Store Record Collection to expose as a Text Search.

    Preferably the class methods are used to create an instance of this class.
    Otherwise the search executes in the following order depending on which store was set:
    1. vectorizable_text_search
    2. vector_text_search
    3. vectorized_search (after calling a embedding service)

    Args:
        vectorizable_text_search: A vector store record collection with a method to search for vectorizable text.
        vectorized_search: A vector store record collection with a method to search for vectors.
        vector_text_search: A vector store record collection with a method to search for text.
        embedding_service: An embedding service to use for vectorized search.
        string_mapper: A function to map a record to a string.
        text_search_results_mapper: A function to map a record to a TextSearchResult.

    """

    vectorizable_text_search: VectorizableTextSearchMixin | None = None
    vectorized_search: VectorizedSearchMixin | None = None
    vector_text_search: VectorTextSearchMixin | None = None
    embedding_service: EmbeddingGeneratorBase | None = None
    string_mapper: Callable[[TModel], str] | None = None
    text_search_results_mapper: Callable[[TModel], TextSearchResult] | None = None

    @model_validator(mode="before")
    @classmethod
    def _validate_stores(cls, data: Any) -> dict[str, Any]:
        """Validate the capabilities."""
        if isinstance(data, dict):
            if (
                not data.get("vectorizable_text_search")
                and not data.get("vectorized_search")
                and not data.get("vector_text_search")
            ):
                raise VectorStoreInitializationException(
                    "At least one of vectorizable_text_search, vectorized_search or vector_text_search is required."
                )
            if data.get("vectorized_search") and not data.get("embedding_service"):
                raise VectorStoreInitializationException("embedding_service is required when using vectorized_search.")
        return data

    @classmethod
    def from_vectorizable_text_search(
        cls: type[_T],
        vectorizable_text_search: VectorizableTextSearchMixin,
        string_mapper: Callable | None = None,
        text_search_results_mapper: Callable | None = None,
        **kwargs: Any,
    ) -> _T:
        """Create a new VectorStoreTextSearch from a VectorStoreRecordCollection."""
        return cls(
            vectorizable_text_search=vectorizable_text_search,
            string_mapper=string_mapper,
            text_search_results_mapper=text_search_results_mapper,
            **kwargs,
        )

    @classmethod
    def from_vectorized_search(
        cls: type[_T],
        vectorized_search: VectorizedSearchMixin,
        embedding_service: EmbeddingGeneratorBase,
        string_mapper: Callable | None = None,
        text_search_results_mapper: Callable | None = None,
        **kwargs: Any,
    ) -> _T:
        """Create a new VectorStoreTextSearch from a VectorStoreRecordCollection."""
        return cls(
            vectorized_search=vectorized_search,
            embedding_service=embedding_service,
            string_mapper=string_mapper,
            text_search_results_mapper=text_search_results_mapper,
            **kwargs,
        )

    @classmethod
    def from_vector_text_search(
        cls: type[_T],
        vector_text_search: VectorTextSearchMixin,
        string_mapper: Callable | None = None,
        text_search_results_mapper: Callable | None = None,
        **kwargs: Any,
    ) -> _T:
        """Create a new VectorStoreTextSearch from a VectorStoreRecordCollection."""
        return cls(
            vector_text_search=vector_text_search,
            string_mapper=string_mapper,
            text_search_results_mapper=text_search_results_mapper,
            **kwargs,
        )

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
        if self.vectorizable_text_search:
            return await self.vectorizable_text_search.vectorizable_text_search(
                vectorizable_text=query, options=options, **kwargs
            )
        if self.vector_text_search:
            return await self.vector_text_search.text_search(search_text=query, options=options, **kwargs)
        if self.vectorized_search and self.embedding_service:
            return await self.vectorized_search.vectorized_search(
                vector=(await self.embedding_service.generate_raw_embeddings([query]))[0],
                options=options,
                **kwargs,
            )
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
