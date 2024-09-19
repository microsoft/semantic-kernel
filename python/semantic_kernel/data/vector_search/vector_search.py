# Copyright (c) Microsoft. All rights reserved.

import json
import logging
from abc import abstractmethod
from collections.abc import Awaitable, Callable, Mapping, Sequence
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

from semantic_kernel.data.kernel_search_result import KernelSearchResult
from semantic_kernel.data.search_base import SearchBase
from semantic_kernel.data.search_options_base import SearchOptions
from semantic_kernel.data.vector_search.vector_search_options import VectorSearchOptions
from semantic_kernel.data.vector_search.vector_search_result import VectorSearchResult
from semantic_kernel.data.vector_storage.vector_store_record_collection import VectorStoreRecordCollection
from semantic_kernel.functions.kernel_parameter_metadata import KernelParameterMetadata
from semantic_kernel.utils.experimental_decorator import experimental_class

TModel = TypeVar("TModel")
TKey = TypeVar("TKey")

logger = logging.getLogger(__name__)


@experimental_class
class VectorSearch(VectorStoreRecordCollection[TKey, TModel], SearchBase, Generic[TKey, TModel]):
    """Method for searching vectors."""

    # region: New abstract methods to be implemented by vector stores

    @abstractmethod
    async def _inner_search(
        self,
        options: SearchOptions | None = None,
        **kwargs: Any,
    ) -> Sequence[Mapping[str, Any | float | None]] | None:
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

    async def search(
        self,
        options: SearchOptions | None = None,
        **kwargs: Any,
    ) -> KernelSearchResult[str]:
        """Search for vectors similar to the query."""
        if not options:
            options = self._create_options(**kwargs)
        raw_results = await self._inner_search(options=options)
        if raw_results is None or len(raw_results) == 0:
            return KernelSearchResult(results=[], total_count=0)
        return KernelSearchResult(
            results=self._get_strings_from_records(self._get_records_from_results(raw_results)),
            total_count=len(raw_results),
            metadata=self._get_metadata_from_results(raw_results),
        )

    async def get_search_result(
        self,
        options: SearchOptions | None = None,
        **kwargs: Any,
    ) -> KernelSearchResult[Any]:
        """Search for text, returning a KernelSearchResult with the results directly from the service."""
        if not options:
            options = self._create_options(**kwargs)
        raw_results = await self._inner_search(options=options)
        if raw_results is None or len(raw_results) == 0:
            return KernelSearchResult(results=[], total_count=0)
        return KernelSearchResult(
            results=raw_results,
            total_count=len(raw_results),
            metadata=self._get_metadata_from_results(raw_results),
        )

    @staticmethod
    def _default_parameter_metadata() -> list[KernelParameterMetadata]:
        """Default parameter metadata for text search functions.

        This function should be overridden by subclasses.
        """
        return []

    @property
    def _get_options_class(self) -> type[SearchOptions]:
        return VectorSearchOptions

    @property
    def _search_function_map(self) -> dict[str, Callable[..., Awaitable[KernelSearchResult[Any]]]]:
        """Get the search function map.

        Can be overwritten by subclasses.
        """
        return {
            "search": self.search,
            "get_vector_search_result": self.get_vector_search_result,
            "get_vector_search_results": self.get_vector_search_result,
            "get_search_result": self.get_search_result,
            "get_search_results": self.get_search_result,
        }

    # endregion
    # region: New methods

    async def get_vector_search_result(
        self,
        options: SearchOptions | None = None,
        **kwargs: Any,
    ) -> KernelSearchResult[VectorSearchResult[TModel]]:
        """Search for text, returning a KernelSearchResult with VectorSearchResults."""
        if not options:
            options = self._create_options(**kwargs)
        raw_results = await self._inner_search(options=options)
        if raw_results is None or len(raw_results) == 0:
            return KernelSearchResult(results=[], total_count=0)
        return KernelSearchResult(
            results=self._get_vector_search_results_from_results(raw_results),
            total_count=len(raw_results),
            metadata=self._get_metadata_from_results(raw_results),
        )

    def _get_strings_from_records(self, records: Sequence[TModel]) -> Sequence[str]:
        return [record.model_dump_json() if isinstance(record, BaseModel) else json.dumps(record) for record in records]

    def _get_records_from_results(self, results: Sequence[Any]) -> Sequence[TModel]:
        return [self.deserialize(self._get_record_from_result(res)) for res in results]  # type: ignore

    def _get_vector_search_results_from_results(self, results: Sequence[Any]) -> Sequence[VectorSearchResult[TModel]]:
        scores = [self._get_score_from_result(res) for res in results]
        records = self.deserialize(self._get_records_from_results(results))
        if records is None:
            return []
        if not isinstance(records, Sequence):
            # this means this is a container of records
            # scores are ignored
            return [VectorSearchResult(record=records, score=None)]
        return [
            VectorSearchResult(
                record=record,
                score=score,
            )
            for record, score in zip(records, scores)
        ]

    def _get_metadata_from_results(self, results: Sequence[Any]) -> dict[str, Any]:
        return {"scores": [self._get_score_from_result(res) for res in results]}
