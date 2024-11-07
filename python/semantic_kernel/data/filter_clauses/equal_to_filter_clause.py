# Copyright (c) Microsoft. All rights reserved.

from pydantic import Field

from semantic_kernel.data.filter_clauses.filter_clause_base import FilterClauseBase
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class EqualTo(FilterClauseBase):
    """A filter clause for an equals comparison.

    Args:
        field_name: The name of the field to compare.
        value: The value to compare against the field.

    """

    filter_clause_type: str = Field("equal_to", init=False)  # type: ignore
