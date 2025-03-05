# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.data.search_filter import SearchFilter
from semantic_kernel.utils.feature_stage_decorator import experimental


@experimental
class TextSearchFilter(SearchFilter):
    """A filter clause for a text search query."""

    pass
