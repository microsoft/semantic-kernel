# Copyright (c) Microsoft. All rights reserved.


from semantic_kernel.data.filters.search_filter_base import SearchFilter
from semantic_kernel.kernel_pydantic import KernelBaseModel


class SearchOptions(KernelBaseModel):
    """Options for a search."""

    filter: SearchFilter | None = None
