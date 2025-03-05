# Copyright (c) Microsoft. All rights reserved.


from pydantic import Field

from semantic_kernel.data.search_filter import SearchFilter
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class SearchOptions(KernelBaseModel):
    """Options for a search."""

    filter: SearchFilter = Field(default_factory=SearchFilter)
    include_total_count: bool = False
