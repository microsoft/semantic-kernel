# Copyright (c) Microsoft. All rights reserved.

import logging
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from semantic_kernel.data.text_search.utils import create_options
from semantic_kernel.exceptions import (
    VectorSearchExecutionException,
    VectorSearchOptionsException,
    VectorStoreMixinException,
    VectorStoreModelDeserializationException,
)
from semantic_kernel.utils.experimental_decorator import experimental_class

if TYPE_CHECKING:
    from semantic_kernel.data.kernel_search_results import KernelSearchResults
    from semantic_kernel.data.search_options import SearchOptions
    from semantic_kernel.data.vector_search.vector_search_result import VectorSearchResult

TModel = TypeVar("TModel")

logger = logging.getLogger(__name__)


@experimental_class
class VectorizedSearchMixin(Generic[TModel]):
    """The mixin for searching with vectors. To be used in combination with VectorSearchBase."""

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
        from semantic_kernel.data.vector_search.vector_search import VectorSearchBase

        if not isinstance(self, VectorSearchBase):
            raise VectorStoreMixinException("This method can only be used in combination with the VectorSearchBase.")
        options = create_options(self.options_class, options, **kwargs)
        try:
            return await self._inner_search(vector=vector, options=options)  # type: ignore
        except (VectorStoreModelDeserializationException, VectorSearchOptionsException, VectorSearchExecutionException):
            raise  # pragma: no cover
        except Exception as exc:
            raise VectorSearchExecutionException(f"An error occurred during the search: {exc}") from exc
