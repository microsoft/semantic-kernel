# Copyright (c) Microsoft. All rights reserved.


from abc import ABC

from pydantic import Field

from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class FilterClauseBase(ABC, KernelBaseModel):
    """A base for all filter clauses."""

    filter_clause_type: str = Field("BaseFilterClause", init=False)  # type: ignore
