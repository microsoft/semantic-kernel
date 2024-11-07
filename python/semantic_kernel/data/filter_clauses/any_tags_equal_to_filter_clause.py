# Copyright (c) Microsoft. All rights reserved.


from pydantic import Field

from semantic_kernel.data.filter_clauses.filter_clause_base import FilterClauseBase
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class AnyTagsEqualTo(FilterClauseBase, KernelBaseModel):
    """A filter clause for a any tags equals comparison."""

    filter_clause_type: str = Field("any_tags_equal_to", init=False)  # type: ignore

    field_name: str
    value: str
