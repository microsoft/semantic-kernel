# Copyright (c) Microsoft. All rights reserved.

from typing import Literal

from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.search.const import FilterClauseType


class FilterClause(KernelBaseModel):
    """A filter clause for a vector search query."""

    field_name: str
    value: str
    clause_type: Literal[FilterClauseType.EQUALITY, FilterClauseType.TAG_LIST_CONTAINS]
