# Copyright (c) Microsoft. All rights reserved.


from typing import Annotated

from pydantic import Field

from semantic_kernel.data.const import DEFAULT_COUNT
from semantic_kernel.data.search_options_base import SearchOptions
from semantic_kernel.data.text_search.text_search_filter import TextSearchFilter
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class TextSearchOptions(SearchOptions):
    """Options for a text search."""

    query: str | None = None
    filter: TextSearchFilter | None = None
    count: Annotated[int, Field(gt=0)] = DEFAULT_COUNT
    offset: Annotated[int, Field(ge=0)] = 0
    include_total_count: bool = False
