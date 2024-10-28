# Copyright (c) Microsoft. All rights reserved.

import logging
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from semantic_kernel.data.text_search.utils import create_options
from semantic_kernel.utils.experimental_decorator import experimental_class

if TYPE_CHECKING:
    from semantic_kernel.data.kernel_search_results import KernelSearchResults
    from semantic_kernel.data.search_options import SearchOptions
    from semantic_kernel.data.vector_search.vector_search_result import VectorSearchResult

TModel = TypeVar("TModel")

logger = logging.getLogger(__name__)


@experimental_class
class VectorizedSearchMixin(Generic[TModel]):
    """Method for searching vectors."""

    async def vectorized_search(
        self,
        vector: list[float | int],
        options: "SearchOptions | None" = None,
        **kwargs: Any,
    ) -> "KernelSearchResults[VectorSearchResult[TModel]]":
        """Search the vector store for records that match the given embedding and filter.

        Args:
            vector: The vector to search for.
            options: options, should include query_text
            **kwargs: if options are not set, this is used to create them.

        Raises:
            VectorSearchOptionsException: raised when the options given are not correct.
            SearchResultEmptyError: raised when there are no results returned.

        """
        from semantic_kernel.data.vector_search.vector_search import VectorSearchBase

        if isinstance(self, VectorSearchBase):
            options = create_options(self.options_class, options, **kwargs)
            return await self._inner_search(vector=vector, options=options)
        raise NotImplementedError("This method can only be used in combination with the VectorSearchBase.")
