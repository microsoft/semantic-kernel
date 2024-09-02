# Copyright (c) Microsoft. All rights reserved.

from typing import Literal

from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.search.const import FilterClauseType


class FilterClause(KernelBaseModel):
    """A filter clause for a vector search query."""

    field_name: str | None
    value: str | None
    clause_type: Literal[
        FilterClauseType.EQUALITY, FilterClauseType.TAG_LIST_CONTAINS, FilterClauseType.DIRECT, FilterClauseType.PROMPT
    ]
