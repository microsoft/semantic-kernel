# Copyright (c) Microsoft. All rights reserved.

import json
import logging
from abc import abstractmethod
from collections.abc import AsyncIterable, Awaitable, Callable, Sequence
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

from semantic_kernel.data.kernel_search_results import KernelSearchResults
from semantic_kernel.data.search_base import SearchBase
from semantic_kernel.data.search_options_base import SearchOptions
from semantic_kernel.data.vector_search.vector_search_options import VectorSearchOptions
from semantic_kernel.data.vector_search.vector_search_result import VectorSearchResult
from semantic_kernel.data.vector_storage.vector_store_record_collection import VectorStoreRecordCollection
from semantic_kernel.utils.experimental_decorator import experimental_class

TModel = TypeVar("TModel")
TKey = TypeVar("TKey")

logger = logging.getLogger(__name__)


@experimental_class
class VectorSearchBase(VectorStoreRecordCollection[TKey, TModel], SearchBase, Generic[TKey, TModel]):
    """Method for searching vectors."""

    # region: New abstract methods to be implemented by vector stores

    @abstractmethod
    async def _inner_search(
        self,
        options: SearchOptions | None = None,
        search_text: str | None = None,
        vector: list[float | int] | None = None,
        **kwargs: Any,
    ) -> KernelSearchResults[Any]:
        """Inner search method."""
        ...

    @abstractmethod
    def _get_record_from_result(self, result: Any) -> Any:
        """Get the record from the result.

        Does any unpacking or processing of the result to get just the record.
        """
        ...

    @abstractmethod
    def _get_score_from_result(self, result: Any) -> float | None:
        """Get the score from the result."""
        ...

    # endregion
    # region: Implementation of SearchBase

    @property
    def _get_options_class(self) -> type[SearchOptions]:
        return VectorSearchOptions

    # endregion
    # region: New methods

    def _get_strings_from_records(self, records: Sequence[TModel]) -> Sequence[str]:
        return [record.model_dump_json() if isinstance(record, BaseModel) else json.dumps(record) for record in records]

    async def _get_vector_search_results_from_results(
        self, results: AsyncIterable[Any]
    ) -> AsyncIterable[VectorSearchResult[TModel]]:
        async for result in results:
            record = self.deserialize(self._get_record_from_result(result))
            score = self._get_score_from_result(result)
            if record:
                yield VectorSearchResult(record=record, score=score)


@experimental_class
class VectorizableTextSearch(VectorSearchBase, Generic[TKey, TModel]):
    """Method for searching vectors."""

    async def vectorizable_text_search(
        self,
        search_text: str,
        options: SearchOptions | None = None,
        **kwargs: Any,
    ) -> KernelSearchResults[VectorSearchResult[TModel]]:
        """Search the vector store for records that match the given text and filter.

        The text string will be vectorized downstream and used for the vector search.

        Args:
            search_text: The text to search for.
            options: options for the search
            **kwargs: if options are not set, this is used to create them.

        Raises:
            VectorSearchOptionsException: raised when the options given are not correct.
            SearchResultEmptyError: raised when there are no results returned.

        """
        if not options:
            options = self._create_options(**kwargs)
        return await self._inner_search(search_text=search_text, options=options)

    @property
    def _search_function_map(
        self,
    ) -> dict[str, Callable[..., Awaitable[KernelSearchResults[VectorSearchResult[TModel]]]]]:
        """Get the search function map.

        Can be overwritten by subclasses.
        """
        function_map = super()._search_function_map
        function_map["vectorizable_text_search"] = self.vectorizable_text_search
        return function_map


@experimental_class
class VectorizedSearch(VectorSearchBase, Generic[TKey, TModel]):
    """Method for searching vectors."""

    async def vectorized_search(
        self,
        vector: list[float | int],
        options: SearchOptions | None = None,
        **kwargs: Any,
    ) -> KernelSearchResults[VectorSearchResult[TModel]]:
        """Search the vector store for records that match the given embedding and filter.

        Args:
            vector: The vector to search for.
            options: options, should include query_text
            **kwargs: if options are not set, this is used to create them.

        Raises:
            VectorSearchOptionsException: raised when the options given are not correct.
            SearchResultEmptyError: raised when there are no results returned.

        """
        if not options:
            options = self._create_options(**kwargs)
        return await self._inner_search(vector=vector, options=options)

    @property
    def _search_function_map(
        self,
    ) -> dict[str, Callable[..., Awaitable[KernelSearchResults[VectorSearchResult[TModel]]]]]:
        """Get the search function map.

        Can be overwritten by subclasses.
        """
        function_map = super()._search_function_map
        function_map["vectorized_search"] = self.vectorized_search
        return function_map
