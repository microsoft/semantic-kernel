# Copyright (c) Microsoft. All rights reserved.

from abc import abstractmethod
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Generic, Literal, TypeVar

from semantic_kernel.data.const import VectorSearchQueryTypes
from semantic_kernel.data.vector_search_options import VectorSearchOptions
from semantic_kernel.data.vector_search_result import VectorSearchResult
from semantic_kernel.data.vector_store_record_collection import VectorStoreRecordCollection
from semantic_kernel.exceptions import VectorStoreSearchError
from semantic_kernel.utils.experimental_decorator import experimental_class

if TYPE_CHECKING:
    pass

TModel = TypeVar("TModel")
TKey = TypeVar("TKey")


@experimental_class
class VectorSearch(VectorStoreRecordCollection[TKey, TModel], Generic[TKey, TModel]):
    """Method for searching vectors."""

    @abstractmethod
    async def _inner_search(
        self,
        query_type: Literal[
            VectorSearchQueryTypes.VECTORIZED_SEARCH_QUERY,
            VectorSearchQueryTypes.VECTORIZABLE_TEXT_SEARCH_QUERY,
            VectorSearchQueryTypes.HYBRID_TEXT_VECTORIZED_SEARCH_QUERY,
            VectorSearchQueryTypes.HYBRID_VECTORIZABLE_TEXT_SEARCH_QUERY,
        ],
        search_options: VectorSearchOptions,
        query_text: str | None = None,
        vector: list[float | int] | None = None,
        **kwargs: Any,
    ) -> Sequence[tuple[Any, float | None]] | None:
        """Inner search method."""
        ...

    async def search(
        self,
        query_type: Literal[
            VectorSearchQueryTypes.VECTORIZED_SEARCH_QUERY,
            VectorSearchQueryTypes.VECTORIZABLE_TEXT_SEARCH_QUERY,
            VectorSearchQueryTypes.HYBRID_TEXT_VECTORIZED_SEARCH_QUERY,
            VectorSearchQueryTypes.HYBRID_VECTORIZABLE_TEXT_SEARCH_QUERY,
        ],
        query_text: str | None = None,
        vector: list[float | int] | None = None,
        search_options: VectorSearchOptions = VectorSearchOptions(),
        **kwargs: Any,
    ) -> Sequence[VectorSearchResult[TModel]] | None:
        """Search for vectors similar to the query."""
        try:
            records = await self._inner_search(
                query_type=query_type, search_options=search_options, query_text=query_text, vector=vector, **kwargs
            )
        except Exception as exc:
            raise VectorStoreSearchError(f"Error getting records: {exc}") from exc

        if not records:
            return None

        try:
            return [VectorSearchResult(record=self.deserialize(record), score=score) for record, score in records]
        except Exception as exc:
            raise VectorStoreSearchError(f"Error deserializing record: {exc}") from exc
