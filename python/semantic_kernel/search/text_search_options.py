# Copyright (c) Microsoft. All rights reserved.


from typing import Annotated

from pydantic import Field

from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.search.const import DEFAULT_COUNT
from semantic_kernel.search.filter_clause import FilterClause


class TextSearchOptions(KernelBaseModel):
    """Options for a text search."""

    query: str | None = None
    search_filters: list[FilterClause] = Field(default_factory=list)
    count: Annotated[int, Field(gt=0)] = DEFAULT_COUNT
    offset: Annotated[int, Field(ge=0)] = 0
    include_total_count: bool = False
