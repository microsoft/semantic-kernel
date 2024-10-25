# Copyright (c) Microsoft. All rights reserved.

import json
import logging
from abc import abstractmethod
from collections.abc import AsyncIterable, Awaitable, Callable, Sequence
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

from semantic_kernel.data.kernel_search_results import KernelSearchResults
from semantic_kernel.data.search_options import SearchOptions
from semantic_kernel.data.vector_search.vector_search_options import VectorSearchOptions
from semantic_kernel.data.vector_search.vector_search_result import VectorSearchResult
from semantic_kernel.data.vector_search.vector_text_search import VectorTextSearchMixin
from semantic_kernel.data.vector_storage.vector_store_record_collection import VectorStoreRecordCollection
from semantic_kernel.utils.experimental_decorator import experimental_class

TModel = TypeVar("TModel")
TKey = TypeVar("TKey")

logger = logging.getLogger(__name__)


@experimental_class
class VectorSearchBase(VectorStoreRecordCollection[TKey, TModel], Generic[TKey, TModel]):
    """Method for searching vectors."""

    # region: New abstract methods to be implemented by vector stores

    @abstractmethod
    async def _inner_search(
        self,
        options: SearchOptions | None = None,
        search_text: str | None = None,
        vectorizable_text: str | None = None,
        vector: list[float | int] | None = None,
        **kwargs: Any,
    ) -> KernelSearchResults[Any]:
        """Inner search method.

        The value of the vector_search_type parameter determines the type of search
        to be performed and what type of results is passed back, always wrapped
        in a KernelSearchResults object.

        """
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
                # single records are always returned as single records by the deserializer
                yield VectorSearchResult(record=record, score=score)  # type: ignore

    @property
    def _search_function_map(self) -> dict[str, Callable[..., Awaitable[KernelSearchResults[Any]]]]:
        """Get the search function map.

        Can be overwritten by subclasses.
        """
        from semantic_kernel.data.vector_search.vectorizable_text_search import VectorizableTextSearchMixin
        from semantic_kernel.data.vector_search.vectorized_search import VectorizedSearchMixin

        search_functions = {}
        if isinstance(self, VectorizableTextSearchMixin):
            search_functions["vectorizable_text_search"] = self.vectorizable_text_search
        if isinstance(self, VectorizedSearchMixin):
            search_functions["vectorized_search"] = self.vectorized_search
        if isinstance(self, VectorTextSearchMixin):
            search_functions["text_search"] = self.text_search
        return search_functions
