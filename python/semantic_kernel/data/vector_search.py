# Copyright (c) Microsoft. All rights reserved.

import logging
from abc import abstractmethod
from collections.abc import Mapping, Sequence
from typing import Any, Generic, TypeVar

from pydantic import ValidationError

from semantic_kernel.data.vector_search_options import VectorSearchOptions
from semantic_kernel.data.vector_search_result import VectorSearchResult
from semantic_kernel.data.vector_store_record_collection import VectorStoreRecordCollection
from semantic_kernel.exceptions import VectorStoreSearchError
from semantic_kernel.kernel_types import OneOrMany
from semantic_kernel.search.kernel_search_result import KernelSearchResult
from semantic_kernel.search.text_search import TextSearch
from semantic_kernel.search.text_search_result import TextSearchResult
from semantic_kernel.utils.experimental_decorator import experimental_class

TModel = TypeVar("TModel")
TKey = TypeVar("TKey")

logger = logging.getLogger(__name__)


@experimental_class
class VectorSearch(VectorStoreRecordCollection[TKey, TModel], Generic[TKey, TModel], TextSearch):
    """Method for searching vectors."""

    @abstractmethod
    async def _inner_search(
        self,
        options: VectorSearchOptions | None = None,
        query_text: str | None = None,
        vector: list[float | int] | None = None,
        **kwargs: Any,
    ) -> Sequence[Mapping[str, Any | float | None]] | None:
        """Inner search method."""
        ...

    async def _wrap_inner(
        self,
        query: str | None = None,
        options: VectorSearchOptions | None = None,
        vector: list[float | int] | None = None,
        **kwargs: Any,
    ) -> tuple[Sequence[Mapping[str, Any | float | None]], int]:
        try:
            records = await self._inner_search(options=options, query_text=query, vector=vector, **kwargs)
            return (records, len(records)) if records else ([], 0)
        except Exception as exc:
            raise VectorStoreSearchError(f"Error getting records: {exc}") from exc

    async def search(
        self,
        query: str | None = None,
        options: VectorSearchOptions | None = None,
        vector: list[float | int] | None = None,
        **kwargs: Any,
    ) -> KernelSearchResult[str]:
        """Search for vectors similar to the query."""
        options = self._get_options(options, **kwargs)
        records, count = await self._wrap_inner(query=query, options=options, vector=vector)
        if count == 0:
            return KernelSearchResult(results=[], total_count=count)
        results: list[str] = []
        metadata: dict[str, Any] = {}
        metadata["scores"] = []
        for record in records:
            try:
                rec = self.deserialize(record["record"])
            except Exception as exc:
                raise VectorStoreSearchError(f"Error deserializing record: {exc}") from exc
            if isinstance(rec, Sequence):
                rec = rec[0]
            results.append(rec)
            metadata["scores"].append(record["score"])
        return KernelSearchResult(
            results=results,
            total_count=count,
            metadata=metadata,
        )

    async def get_text_search_result(
        self,
        query: str,
        options: VectorSearchOptions = VectorSearchOptions(),
        vector: list[float | int] | None = None,
        **kwargs: Any,
    ) -> KernelSearchResult[TextSearchResult]:
        """Search for text, returning a KernelSearchResult with TextSearchResults."""
        raise NotImplementedError(
            "get_text_search_result is not implemented for VectorSearch, "
            "use `search` for strings, or `get_search_result` for vector search results with the data model."
        )

    async def get_search_result(
        self,
        query: str,
        options: VectorSearchOptions = VectorSearchOptions(),
        vector: list[float | int] | None = None,
        **kwargs: Any,
    ) -> KernelSearchResult[VectorSearchResult[TModel]]:
        """Search for text, returning a KernelSearchResult with the results directly from the service."""
        records, count = await self._wrap_inner(query=query, options=options, vector=vector, **kwargs)
        if count == 0:
            return KernelSearchResult(results=[], total_count=count)
        if not options.string_content_field_name:
            raise VectorStoreSearchError("string_content_field_name is required for search")
        results: list[VectorSearchResult[TModel]] = []
        for record in records:
            try:
                rec: OneOrMany[TModel] = self.deserialize(record)
            except Exception as exc:
                raise VectorStoreSearchError(f"Error deserializing record: {exc}") from exc
            if not rec:
                continue
            results.append(
                VectorSearchResult(
                    record=rec[0] if isinstance(rec, Sequence) else rec,
                    score=record["score"],
                )
            )
        return KernelSearchResult(results=results, total_count=count)

    def _get_options(self, options: VectorSearchOptions | None, **kwargs: Any) -> VectorSearchOptions:
        if options is not None:
            return options
        try:
            return VectorSearchOptions(**kwargs)
        except ValidationError:
            return VectorSearchOptions()
