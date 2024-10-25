# Copyright (c) Microsoft. All rights reserved.

import logging
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from semantic_kernel.utils.experimental_decorator import experimental_class

if TYPE_CHECKING:
    from semantic_kernel.data.kernel_search_results import KernelSearchResults
    from semantic_kernel.data.search_options import SearchOptions
    from semantic_kernel.data.vector_search.vector_search_result import VectorSearchResult

TModel = TypeVar("TModel")

logger = logging.getLogger(__name__)


@experimental_class
class VectorizableTextSearchMixin(Generic[TModel]):
    """Method for searching vectors."""

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
            VectorSearchOptionsException: raised when the options given are not correct.
            SearchResultEmptyError: raised when there are no results returned.

        """
        from semantic_kernel.data.vector_search.vector_search import VectorSearchBase

        if isinstance(self, VectorSearchBase):
            if not options:
                options = self._create_options(**kwargs)
            return await self._inner_search(vectorizable_text=vectorizable_text, options=options)
        raise NotImplementedError("This method can only be used in combination with the VectorSearchBase.")
