# Copyright (c) Microsoft. All rights reserved.

import json
import logging
from abc import abstractmethod
from collections.abc import Mapping, Sequence
from typing import Any, Generic, TypeVar, override

from pydantic import ValidationError

from semantic_kernel.data.vector_search_options import VectorSearchOptions
from semantic_kernel.data.vector_search_result import VectorSearchResult
from semantic_kernel.data.vector_store_record_collection import VectorStoreRecordCollection
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
        **kwargs: Any,
    ) -> Sequence[Mapping[str, Any | float | None]] | None:
        """Inner search method."""
        ...

    async def search(
        self,
        options: VectorSearchOptions | None = None,
        **kwargs: Any,
    ) -> KernelSearchResult[str]:
        """Search for vectors similar to the query."""
        options = self._create_options(**kwargs)
        raw_results = await self._inner_search(options=options)
        if raw_results is None or len(raw_results) == 0:
            return KernelSearchResult(results=[], total_count=0)
        return KernelSearchResult(
            results=self._get_strings_from_records(self._get_records_from_results(raw_results)),
            total_count=len(raw_results),
            metadata=self._get_metadata_from_results(raw_results),
        )

    async def get_text_search_result(
        self,
        options: VectorSearchOptions = VectorSearchOptions(),
        **kwargs: Any,
    ) -> KernelSearchResult[TextSearchResult]:
        """Search for text, returning a KernelSearchResult with TextSearchResults."""
        raise NotImplementedError(
            "get_text_search_result is not implemented for VectorSearch, "
            "use `search` for strings, or `get_search_result` for vector search results with the data model."
        )

    async def get_vector_search_result(
        self,
        options: VectorSearchOptions = VectorSearchOptions(),
        **kwargs: Any,
    ) -> KernelSearchResult[VectorSearchResult[TModel]]:
        """Search for text, returning a KernelSearchResult with VectorSearchResults."""
        options = self._create_options(**kwargs)
        raw_results = await self._inner_search(options=options)
        if raw_results is None or len(raw_results) == 0:
            return KernelSearchResult(results=[], total_count=0)
        return KernelSearchResult(
            results=self._get_vector_search_results_from_results(raw_results),
            total_count=len(raw_results),
            metadata=self._get_metadata_from_results(raw_results),
        )

    async def get_search_result(
        self,
        options: VectorSearchOptions = VectorSearchOptions(),
        **kwargs: Any,
    ) -> KernelSearchResult[Any]:
        """Search for text, returning a KernelSearchResult with the results directly from the service."""
        options = self._create_options(**kwargs)
        raw_results = await self._inner_search(options=options)
        if raw_results is None or len(raw_results) == 0:
            return KernelSearchResult(results=[], total_count=0)
        return KernelSearchResult(
            results=raw_results,
            total_count=len(raw_results),
            metadata=self._get_metadata_from_results(raw_results),
        )

    @override
    def _create_options(self, **kwargs: Any) -> VectorSearchOptions:
        try:
            logger.debug(f"Creating VectorSearchOptions with kwargs: {kwargs}")
            return VectorSearchOptions(**kwargs)
        except ValidationError:
            return VectorSearchOptions()

    def _get_strings_from_records(self, records: Sequence[TModel]) -> Sequence[str]:
        return [json.dumps(record) for record in records]

    def _get_records_from_results(self, results: Sequence[Any]) -> Sequence[TModel]:
        return [self.deserialize(self._get_record_from_result(res)) for res in results]

    def _get_vector_search_results_from_results(self, results: Sequence[Any]) -> Sequence[VectorSearchResult[TModel]]:
        return [
            VectorSearchResult(
                record=self.deserialize(self._get_record_from_result(res)),
                score=self._get_score_from_result(res),
            )
            for res in results
        ]

    def _get_metadata_from_results(self, results: Sequence[Any]) -> dict[str, Any]:
        return {"scores": [self._get_score_from_result(res) for res in results]}

    @abstractmethod
    def _get_record_from_result(self, result: Any) -> Any:
        """Get the record from the result."""
        ...

    @abstractmethod
    def _get_score_from_result(self, result: Any) -> float:
        """Get the score from the result."""
        ...
