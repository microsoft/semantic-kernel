# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.data.search_filter import SearchFilter
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class TextSearchFilter(SearchFilter):
    """A filter clause for a text search query."""

    pass
