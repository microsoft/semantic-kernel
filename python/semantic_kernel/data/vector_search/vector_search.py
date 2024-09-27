# Copyright (c) Microsoft. All rights reserved.

import json
import logging
from abc import abstractmethod
from collections.abc import Awaitable, Callable, Mapping, Sequence
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

from semantic_kernel.data.kernel_search_result import KernelSearchResults
from semantic_kernel.data.search_base import SearchBase
from semantic_kernel.data.search_options_base import SearchOptions
from semantic_kernel.data.vector_search.const import VectorSearchQueryTypes
from semantic_kernel.data.vector_search.vector_search_options import VectorSearchOptions
from semantic_kernel.data.vector_search.vector_search_result import VectorSearchResult
from semantic_kernel.data.vector_storage.vector_store_record_collection import VectorStoreRecordCollection
from semantic_kernel.exceptions.search_exceptions import SearchResultEmptyError, VectorSearchOptionsException
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
    def _search_function_map(
        self,
    ) -> dict[str, Callable[..., Awaitable[KernelSearchResults[VectorSearchResult[TModel]]]]]:
        """Get the search function map.

        Can be overwritten by subclasses.
        """
        return {"vectorizable_text_search": self.vectorizable_text_search, "vectorized_search": self.vectorized_search}

    # endregion
    # region: New methods

    async def vectorizable_text_search(
        self,
        options: SearchOptions | None = None,
        **kwargs: Any,
    ) -> KernelSearchResults[VectorSearchResult[TModel]]:
        """Search the vector store for records that match the given text and filter.

        The text string will be vectorized downstream and used for the vector search.

        Args:
            options: options, should include query
            **kwargs: if options are not set, this is used to create them.

        Raises:
            VectorSearchOptionsException: raised when the options given are not correct.
            SearchResultEmptyError: raised when there are no results returned.

        """
        if not options:
            options = self._create_options(**kwargs)
        if not isinstance(options, VectorSearchOptions) or options.query is None:
            raise VectorSearchOptionsException(
                "Invalid options received, options should be of type "
                "VectorSearchOptions and 'query' should not be None."
            )
        options.query_type = VectorSearchQueryTypes.VECTORIZABLE_TEXT_SEARCH_QUERY
        raw_results = await self._inner_search(options=options)
        if raw_results is None or len(raw_results) == 0:
            raise SearchResultEmptyError("No results returned.")
        return KernelSearchResults(
            results=self._get_vector_search_results_from_results(raw_results),
            total_count=len(raw_results),
            metadata=self._get_metadata_from_results(raw_results),
        )

    async def vectorized_search(
        self,
        options: SearchOptions | None = None,
        **kwargs: Any,
    ) -> KernelSearchResults[VectorSearchResult[TModel]]:
        """Search the vector store for records that match the given embedding and filter.

        Args:
            options: options, should include query_text
            **kwargs: if options are not set, this is used to create them.

        Raises:
            VectorSearchOptionsException: raised when the options given are not correct.
            SearchResultEmptyError: raised when there are no results returned.

        """
        if not options:
            options = self._create_options(**kwargs)
        if not isinstance(options, VectorSearchOptions) or options.vector is None:
            raise VectorSearchOptionsException(
                "Invalid options received, options should be of type "
                "VectorSearchOptions and 'vector' should not be None."
            )
        options.query_type = VectorSearchQueryTypes.VECTORIZED_SEARCH_QUERY
        raw_results = await self._inner_search(options=options)
        if raw_results is None or len(raw_results) == 0:
            raise SearchResultEmptyError("No results returned.")
        return KernelSearchResults(
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
