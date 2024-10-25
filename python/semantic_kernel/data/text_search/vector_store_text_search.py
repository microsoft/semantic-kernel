# Copyright (c) Microsoft. All rights reserved.

from collections.abc import AsyncIterable, Callable
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from pydantic import model_validator

from semantic_kernel.connectors.ai.embeddings.embedding_generator_base import EmbeddingGeneratorBase
from semantic_kernel.data.kernel_search_results import KernelSearchResults
from semantic_kernel.data.text_search.text_search import TextSearch
from semantic_kernel.data.text_search.text_search_result import TextSearchResult
from semantic_kernel.data.vector_search.vector_search_options import VectorSearchOptions
from semantic_kernel.data.vector_search.vector_search_result import VectorSearchResult
from semantic_kernel.data.vector_search.vector_text_search import VectorTextSearchMixin
from semantic_kernel.data.vector_search.vectorizable_text_search import VectorizableTextSearchMixin
from semantic_kernel.data.vector_search.vectorized_search import VectorizedSearchMixin
from semantic_kernel.kernel_pydantic import KernelBaseModel

if TYPE_CHECKING:
    from semantic_kernel.data.search_options import SearchOptions

TModel = TypeVar("TModel")
_T = TypeVar("_T")


class VectorStoreTextSearch(KernelBaseModel, TextSearch, Generic[TModel]):
    """Class that wraps a Vector Store Record Collection to expose as a Text Search."""

    vectorizable_text_search: VectorizableTextSearchMixin | None = None
    vectorized_search: VectorizedSearchMixin | None = None
    text_search: VectorTextSearchMixin | None = None
    embedding_service: EmbeddingGeneratorBase | None = None
    string_mapper: Callable[[TModel], str] | None = None
    text_results_mapper: Callable[[TModel], TextSearchResult] | None = None
    options: VectorSearchOptions | None = None

    @model_validator(mode="before")
    @classmethod
    def validate_setup(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Validate the setup of the VectorStoreTextSearch."""
        if not any([
            data.get("vectorizable_text_search"),
            data.get("vectorized_search"),
            data.get("text_search"),
        ]):
            raise ValueError("One of vectorizable_text_search, vectorized_search, or text_search must be set.")
        if not data.get("embedding_service") and data.get("vectorized_search"):
            raise ValueError("embedding_service must be set if vectorized_search is set.")
        return data

    @classmethod
    def from_vectorizable_text_search(
        cls: type[_T],
        vectorizable_text_search: VectorizableTextSearchMixin,
        string_mapper: Callable | None = None,
        text_results_mapper: Callable | None = None,
        **kwargs: Any,
    ) -> _T:
        """Create a new VectorStoreTextSearch from a VectorStoreRecordCollection."""
        return cls(
            vectorizable_text_search=vectorizable_text_search,
            string_mapper=string_mapper,
            text_results_mapper=text_results_mapper,
            **kwargs,
        )

    @classmethod
    def from_vectorized_search(
        cls: type[_T],
        vectorized_search: VectorizedSearchMixin,
        embedding_service: EmbeddingGeneratorBase,
        string_mapper: Callable | None = None,
        text_results_mapper: Callable | None = None,
        **kwargs: Any,
    ) -> _T:
        """Create a new VectorStoreTextSearch from a VectorStoreRecordCollection."""
        return cls(
            vectorized_search=vectorized_search,
            embedding_service=embedding_service,
            string_mapper=string_mapper,
            text_results_mapper=text_results_mapper,
            **kwargs,
        )

    @classmethod
    def from_text_search(
        cls: type[_T],
        text_search: VectorTextSearchMixin,
        string_mapper: Callable | None = None,
        text_results_mapper: Callable | None = None,
        **kwargs: Any,
    ) -> _T:
        """Create a new VectorStoreTextSearch from a VectorStoreRecordCollection."""
        return cls(
            text_search=text_search,
            string_mapper=string_mapper,
            text_results_mapper=text_results_mapper,
            **kwargs,
        )

    async def search(self, query: str, options=None, **kwargs) -> "KernelSearchResults[str]":
        """Search for text, returning a KernelSearchResult with a list of strings."""
        search_results = await self._execute_search(query, options)
        return KernelSearchResults(
            results=self._get_results_as_strings(search_results.results),
            total_count=search_results.total_count,
            metadata=search_results.metadata,
        )

    async def _execute_search(self, query, options) -> KernelSearchResults[VectorSearchResult[TModel]]:
        """Internal method to execute the search."""
        if self.vectorizable_text_search:
            return await self.vectorizable_text_search.vectorizable_text_search(
                vectorizable_text=query, options=options
            )
        if self.text_search:
            return await self.text_search.text_search(search_text=query, options=options)
        if self.vectorized_search and self.embedding_service:
            embeddings = await self.embedding_service.generate_embeddings([query])
            return await self.vectorized_search.vectorized_search(vector=embeddings[0], options=options)
        raise ValueError("No search method set.")

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
        if self.text_results_mapper:
            async for result in results:
                if result.record:
                    yield self.text_results_mapper(result.record)
            return
        async for result in results:
            if result.record:
                yield TextSearchResult(value=self._default_map_to_string(result.record))

    @property
    def _get_options_class(self) -> type["SearchOptions"]:
        return VectorSearchOptions
