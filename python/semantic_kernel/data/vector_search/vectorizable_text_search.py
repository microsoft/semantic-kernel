# Copyright (c) Microsoft. All rights reserved.

import logging
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from semantic_kernel.data.text_search.utils import create_options
from semantic_kernel.exceptions import VectorStoreMixinException
from semantic_kernel.utils.experimental_decorator import experimental_class

if TYPE_CHECKING:
    from semantic_kernel.data.kernel_search_results import KernelSearchResults
    from semantic_kernel.data.search_options import SearchOptions
    from semantic_kernel.data.vector_search.vector_search_result import VectorSearchResult

TModel = TypeVar("TModel")

logger = logging.getLogger(__name__)


@experimental_class
class VectorizableTextSearchMixin(Generic[TModel]):
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
            VectorSearchOptionsException: raised when the options given are not correct.
            SearchResultEmptyError: raised when there are no results returned.

        """
        from semantic_kernel.data.vector_search.vector_search import VectorSearchBase

        if not isinstance(self, VectorSearchBase):
            raise VectorStoreMixinException("This method can only be used in combination with the VectorSearchBase.")
        options = create_options(self.options_class, options, **kwargs)
        return await self._inner_search(vectorizable_text=vectorizable_text, options=options)  # type: ignore
