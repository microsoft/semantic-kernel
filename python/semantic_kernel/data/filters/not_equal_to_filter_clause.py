# Copyright (c) Microsoft. All rights reserved.


from pydantic import Field

from semantic_kernel.data.filters.filter_clause_base import FilterClauseBase
from semantic_kernel.kernel_pydantic import KernelBaseModel


class NotEqualTo(FilterClauseBase, KernelBaseModel):
    """A filter clause for a not equals comparison."""

    filter_clause_type: str = Field("not_equal_to", init=False)  # type: ignore

    field_name: str
    value: str
