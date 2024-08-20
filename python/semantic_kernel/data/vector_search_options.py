# Copyright (c) Microsoft. All rights reserved.


from pydantic import Field

from semantic_kernel.data.filter_clause import FilterClause
from semantic_kernel.kernel_pydantic import KernelBaseModel


class VectorSearchOptions(KernelBaseModel):
    """Options for vector search."""

    vector_field_name: str | None = None
    vector_search_filters: list[FilterClause] = Field(default_factory=list)
    limit: int = 3
    offset: int = 0
    include_vectors: bool = False
