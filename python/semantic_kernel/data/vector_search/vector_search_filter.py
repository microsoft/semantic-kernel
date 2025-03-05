# Copyright (c) Microsoft. All rights reserved.

import sys

if sys.version_info >= (3, 11):
    from typing import Self  # pragma: no cover
else:
    from typing_extensions import Self  # pragma: no cover

from semantic_kernel.data.filter_clauses.any_tags_equal_to_filter_clause import AnyTagsEqualTo
from semantic_kernel.data.search_filter import SearchFilter
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class VectorSearchFilter(SearchFilter):
    """A filter clause for a vector search query."""

    def __init__(self) -> None:
        """Initialize a new instance of VectorSearchFilter."""
        super().__init__()
        self.any_tag_equal_to = self.__any_tag_equal_to

    def __any_tag_equal_to(self, field_name: str, value: str) -> Self:
        """Adds a filter clause for a any tags equals comparison."""
        self.filters.append(AnyTagsEqualTo(field_name=field_name, value=value))
        return self

    @classmethod
    def any_tag_equal_to(cls, field_name: str, value: str) -> Self:
        """Adds a filter clause for a any tags equals comparison."""
        filter = cls()
        filter.__any_tag_equal_to(field_name=field_name, value=value)
        return filter
