# Copyright (c) Microsoft. All rights reserved.


from typing import Annotated

from pydantic import Field

from semantic_kernel.data.search_options import SearchOptions
from semantic_kernel.data.text_search.text_search_filter import TextSearchFilter
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class TextSearchOptions(SearchOptions):
    """Options for a text search."""

    filter: TextSearchFilter = Field(default_factory=TextSearchFilter)
    top: Annotated[int, Field(gt=0)] = 5
    skip: Annotated[int, Field(ge=0)] = 0
