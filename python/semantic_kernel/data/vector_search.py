# Copyright (c) Microsoft. All rights reserved.

import logging
import sys
from abc import abstractmethod
from collections.abc import AsyncIterable, Callable, Sequence
from typing import TYPE_CHECKING, Annotated, Any, Generic

from pydantic import Field

from semantic_kernel.connectors.ai.embedding_generator_base import EmbeddingGeneratorBase
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.data.record_definition import (
    VectorStoreRecordDataField,
    VectorStoreRecordDefinition,
    VectorStoreRecordVectorField,
)
from semantic_kernel.data.text_search import (
    AnyTagsEqualTo,
    KernelSearchResults,
    SearchFilter,
    SearchOptions,
    TextSearchResult,
    create_options,
)
from semantic_kernel.data.vector_storage import TKey, TModel, VectorStoreRecordHandler
from semantic_kernel.exceptions import (
    VectorSearchExecutionException,
    VectorSearchOptionsException,
    VectorStoreModelDeserializationException,
    VectorStoreModelException,
)
from semantic_kernel.kernel import Kernel
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.kernel_types import OneOrMany
from semantic_kernel.utils.feature_stage_decorator import experimental
from semantic_kernel.utils.list_handler import desync_list

if TYPE_CHECKING:
    from semantic_kernel.data.vector_store_text_search import VectorStoreTextSearch

if sys.version_info >= (3, 11):
    from typing import Self  # pragma: no cover
else:
    from typing_extensions import Self  # pragma: no cover


logger = logging.getLogger(__name__)


# region: Filters


@experimental
class VectorSearchFilter(SearchFilter):
    """A filter clause for a vector search query."""

    def __init__(self) -> None:
        """Initialize a new instance of VectorSearchFilter."""
        super().__init__()
        self.any_tag_equal_to = self.__any_tag_equal_to

    def __any_tag_equal_to(self, field_name: str, value: str) -> Self:
        """Adds a filter clause for a any tags equals comparison."""
        self.filters.append(AnyTagsEqualTo(field_name=field_name, value=value))
        return self

    @classmethod
    def any_tag_equal_to(cls, field_name: str, value: str) -> Self:
        """Adds a filter clause for a any tags equals comparison."""
        filter = cls()
        filter.__any_tag_equal_to(field_name=field_name, value=value)
        return filter


# region: Options


@experimental
class VectorSearchOptions(SearchOptions):
    """Options for vector search, builds on TextSearchOptions."""

    filter: VectorSearchFilter = Field(default_factory=VectorSearchFilter)
    vector_field_name: str | None = None
    top: Annotated[int, Field(gt=0)] = 3
    skip: Annotated[int, Field(ge=0)] = 0
    include_vectors: bool = False


# region: Results


@experimental
class VectorSearchResult(KernelBaseModel, Generic[TModel]):
    """The result of a vector search."""

    record: TModel
    score: float | None = None


# region: Vector Search


@experimental
class VectorSearchBase(VectorStoreRecordHandler[TKey, TModel], Generic[TKey, TModel]):
    """Base class for searching vectors."""

    @property
    def options_class(self) -> type[SearchOptions]:
        """The options class for the search."""
        return VectorSearchOptions

    # region: Abstract methods to be implemented by vector stores

    @abstractmethod
    async def _inner_search(
        self,
        options: VectorSearchOptions,
        search_text: str | None = None,
        vectorizable_text: str | None = None,
        vector: list[float | int] | None = None,
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
            options: The search options, can be None.
            search_text: The text to search for, optional.
            vectorizable_text: The text to search for, will be vectorized downstream, optional.
            vector: The vector to search for, optional.
            **kwargs: Additional arguments that might be needed.

        Returns:
            The search results, wrapped in a KernelSearchResults object.

        Raises:
            VectorSearchExecutionException: If an error occurs during the search.
            VectorStoreModelDeserializationException: If an error occurs during deserialization.
            VectorSearchOptionsException: If the search options are invalid.

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


# region: Vectorized Search


@experimental
class VectorizedSearchMixin(VectorSearchBase[TKey, TModel], Generic[TKey, TModel]):
    """The mixin for searching with vectors."""

    async def vectorized_search(
        self,
        vector: list[float | int],
        options: "SearchOptions | None" = None,
        **kwargs: Any,
    ) -> "KernelSearchResults[VectorSearchResult[TModel]]":
        """Search the vector store for records that match the given vector (embedding) and filter.

        Args:
            vector: The vector to search for.
            options: options, should include query_text
            **kwargs: if options are not set, this is used to create them.

        Raises:
            VectorSearchExecutionException: If an error occurs during the search.
            VectorStoreModelDeserializationException: If an error occurs during deserialization.
            VectorSearchOptionsException: If the search options are invalid.
            VectorStoreMixinException: raised when the method is not used in combination with the VectorSearchBase.

        """
        options = create_options(self.options_class, options, **kwargs)
        try:
            return await self._inner_search(vector=vector, options=options)  # type: ignore
        except (VectorStoreModelDeserializationException, VectorSearchOptionsException, VectorSearchExecutionException):
            raise  # pragma: no cover
        except Exception as exc:
            raise VectorSearchExecutionException(f"An error occurred during the search: {exc}") from exc

    def create_text_search_from_vectorized_search(
        self,
        embedding_service: EmbeddingGeneratorBase,
        string_mapper: Callable[[TModel], str] | None = None,
        text_search_results_mapper: Callable[[TModel], TextSearchResult] | None = None,
    ) -> "VectorStoreTextSearch[TModel]":
        """Create a VectorStoreTextSearch object.

        This method is used to create a VectorStoreTextSearch object that can be used to search the vector store
        for records that match the given text and filter.
        The text string will be vectorized downstream and used for the vector search.

        Args:
            embedding_service: The embedding service to use for vectorizing the text.
            string_mapper: A function that maps the record to a string.
            text_search_results_mapper: A function that maps the record to a TextSearchResult.

        Returns:
            VectorStoreTextSearch: The created VectorStoreTextSearch object.
        """
        from semantic_kernel.data.vector_store_text_search import VectorStoreTextSearch

        return VectorStoreTextSearch.from_vectorized_search(
            self, embedding_service, string_mapper, text_search_results_mapper
        )


# region: Vectorizable Text Search


@experimental
class VectorizableTextSearchMixin(VectorSearchBase[TKey, TModel], Generic[TKey, TModel]):
    """The mixin for searching with text that get's vectorized downstream.

    To be used in combination with VectorSearchBase.
    """

    async def vectorizable_text_search(
        self,
        vectorizable_text: str,
        options: "SearchOptions | None" = None,
        **kwargs: Any,
    ) -> "KernelSearchResults[VectorSearchResult[TModel]]":
        """Search the vector store for records that match the given text and filter.

        The text string will be vectorized downstream and used for the vector search.

        Args:
            vectorizable_text: The text to search for, will be vectorized downstream.
            options: options for the search
            **kwargs: if options are not set, this is used to create them.

        Raises:
            VectorSearchExecutionException: If an error occurs during the search.
            VectorStoreModelDeserializationException: If an error occurs during deserialization.
            VectorSearchOptionsException: If the search options are invalid.
            VectorStoreMixinException: raised when the method is not used in combination with the VectorSearchBase.

        """
        options = create_options(self.options_class, options, **kwargs)  # type: ignore
        try:
            return await self._inner_search(vectorizable_text=vectorizable_text, options=options)  # type: ignore
        except (VectorStoreModelDeserializationException, VectorSearchOptionsException, VectorSearchExecutionException):
            raise  # pragma: no cover
        except Exception as exc:
            raise VectorSearchExecutionException(f"An error occurred during the search: {exc}") from exc

    def create_text_search_from_vectorizable_text_search(
        self,
        string_mapper: Callable[[TModel], str] | None = None,
        text_search_results_mapper: Callable[[TModel], TextSearchResult] | None = None,
    ) -> "VectorStoreTextSearch[TModel]":
        """Create a VectorStoreTextSearch object.

        This method is used to create a VectorStoreTextSearch object that can be used to search the vector store
        for records that match the given text and filter.
        The text string will be vectorized downstream and used for the vector search.

        Args:
            string_mapper: A function that maps the record to a string.
            text_search_results_mapper: A function that maps the record to a TextSearchResult.

        Returns:
            VectorStoreTextSearch: The created VectorStoreTextSearch object.
        """
        from semantic_kernel.data.vector_store_text_search import VectorStoreTextSearch

        return VectorStoreTextSearch.from_vectorizable_text_search(self, string_mapper, text_search_results_mapper)


# region: Vector Text Search


@experimental
class VectorTextSearchMixin(VectorSearchBase[TKey, TModel], Generic[TKey, TModel]):
    """The mixin for text search, to be used in combination with VectorSearchBase."""

    async def text_search(
        self,
        search_text: str,
        options: SearchOptions | None = None,
        **kwargs: Any,
    ) -> "KernelSearchResults[VectorSearchResult[TModel]]":
        """Search the vector store for records that match the given text and filters.

        Args:
            search_text: The query to search for.
            options: options, should include query_text
            **kwargs: if options are not set, this is used to create them.

        Raises:
            VectorSearchExecutionException: If an error occurs during the search.
            VectorStoreModelDeserializationException: If an error occurs during deserialization.
            VectorSearchOptionsException: If the search options are invalid.
            VectorStoreMixinException: raised when the method is not used in combination with the VectorSearchBase.

        """
        options = create_options(self.options_class, options, **kwargs)  # type: ignore
        try:
            return await self._inner_search(search_text=search_text, options=options)  # type: ignore
        except (VectorStoreModelDeserializationException, VectorSearchOptionsException, VectorSearchExecutionException):
            raise  # pragma: no cover
        except Exception as exc:
            raise VectorSearchExecutionException(f"An error occurred during the search: {exc}") from exc

    def create_text_search_from_vector_text_search(
        self,
        string_mapper: Callable[[TModel], str] | None = None,
        text_search_results_mapper: Callable[[TModel], TextSearchResult] | None = None,
    ) -> "VectorStoreTextSearch[TModel]":
        """Create a VectorStoreTextSearch object.

        This method is used to create a VectorStoreTextSearch object that can be used to search the vector store
        for records that match the given text and filter.
        The text string will be vectorized downstream and used for the vector search.

        Args:
            string_mapper: A function that maps the record to a string.
            text_search_results_mapper: A function that maps the record to a TextSearchResult.

        Returns:
            VectorStoreTextSearch: The created VectorStoreTextSearch object.
        """
        from semantic_kernel.data.vector_store_text_search import VectorStoreTextSearch

        return VectorStoreTextSearch.from_vector_text_search(self, string_mapper, text_search_results_mapper)


# region: add_vector_to_records


@experimental
async def add_vector_to_records(
    kernel: "Kernel",
    records: OneOrMany[TModel],
    data_model_type: type | None = None,
    data_model_definition: "VectorStoreRecordDefinition | None" = None,
    **kwargs,
) -> OneOrMany[TModel]:
    """Vectorize the vector record.

    This function can be passed to upsert or upsert batch of a VectorStoreRecordCollection.

    Loops through the fields of the data model definition,
    looks at data fields, if they have a vector field,
    looks up that vector field and checks if is a local embedding.

    If so adds that to a list of embeddings to make.

    Finally calls Kernel add_embedding_to_object with the list of embeddings to make.

    Optional arguments are passed onto the Kernel add_embedding_to_object call.
    """
    # dict of embedding_field.name and tuple of record, settings, field_name
    embeddings_to_make: list[tuple[str, str, dict[str, "PromptExecutionSettings"], Callable | None]] = []
    if not data_model_definition:
        data_model_definition = getattr(data_model_type, "__kernel_vectorstoremodel_definition__", None)
    if not data_model_definition:
        raise VectorStoreModelException(
            "Data model definition is required, either directly or from the data model type."
        )
    for name, field in data_model_definition.fields.items():  # type: ignore
        if (
            not isinstance(field, VectorStoreRecordDataField)
            or not field.has_embedding
            or not field.embedding_property_name
        ):
            continue
        embedding_field = data_model_definition.fields.get(field.embedding_property_name)
        if not isinstance(embedding_field, VectorStoreRecordVectorField):
            raise VectorStoreModelException("Embedding field must be a VectorStoreRecordVectorField")
        if embedding_field.local_embedding:
            embeddings_to_make.append((
                name,
                field.embedding_property_name,
                embedding_field.embedding_settings,
                embedding_field.deserialize_function,
            ))

    for field_to_embed, field_to_store, settings, cast_callable in embeddings_to_make:
        await kernel.add_embedding_to_object(
            inputs=records,
            field_to_embed=field_to_embed,
            field_to_store=field_to_store,
            execution_settings=settings,
            container_mode=data_model_definition.container_mode,
            cast_function=cast_callable,
            **kwargs,
        )
    return records

    # endregion
