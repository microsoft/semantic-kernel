# Copyright (c) Microsoft. All rights reserved.

from typing import Literal

from semantic_kernel.data.const import FilterClauseType
from semantic_kernel.kernel_pydantic import KernelBaseModel


class FilterClause(KernelBaseModel):
    """A filter clause for a vector search query."""

    field_name: str
    value: str
    clause_type: Literal[FilterClauseType.EQUALITY, FilterClauseType.TAG_LIST_CONTAINS]
