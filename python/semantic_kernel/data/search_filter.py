# Copyright (c) Microsoft. All rights reserved.

import sys
from typing import TypeVar

if sys.version_info >= (3, 11):
    from typing import Self  # pragma: no cover
else:
    from typing_extensions import Self  # pragma: no cover

from semantic_kernel.data.filter_clauses.equal_to_filter_clause import EqualTo
from semantic_kernel.data.filter_clauses.filter_clause_base import FilterClauseBase
from semantic_kernel.utils.experimental_decorator import experimental_class

_T = TypeVar("_T", bound="SearchFilter")


@experimental_class
class SearchFilter:
    """A filter clause for a search."""

    def __init__(self) -> None:
        """Initialize a new instance of SearchFilter."""
        self.filters: list[FilterClauseBase] = []
        self.group_type = "AND"
        self.equal_to = self.__equal_to

    def __equal_to(self, field_name: str, value: str) -> Self:
        """Add an equals filter clause."""
        self.filters.append(EqualTo(field_name=field_name, value=value))
        return self

    @classmethod
    def equal_to(cls: type[_T], field_name: str, value: str) -> _T:
        """Add an equals filter clause."""
        filter = cls()
        filter.equal_to(field_name, value)
        return filter

    def __str__(self) -> str:
        """Return a string representation of the filter."""
        return f"{f' {self.group_type} '.join(f'({f!s})' for f in self.filters)}"
