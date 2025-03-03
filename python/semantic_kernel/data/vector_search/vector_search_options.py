# Copyright (c) Microsoft. All rights reserved.


from typing import Annotated

from pydantic import Field

from semantic_kernel.data.search_options import SearchOptions
from semantic_kernel.data.vector_search.vector_search_filter import VectorSearchFilter
from semantic_kernel.utils.feature_stage_decorator import experimental


@experimental
class VectorSearchOptions(SearchOptions):
    """Options for vector search, builds on TextSearchOptions."""

    filter: VectorSearchFilter = Field(default_factory=VectorSearchFilter)
    vector_field_name: str | None = None
    top: Annotated[int, Field(gt=0)] = 3
    skip: Annotated[int, Field(ge=0)] = 0
    include_vectors: bool = False
