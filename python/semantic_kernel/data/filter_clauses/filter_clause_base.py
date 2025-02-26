# Copyright (c) Microsoft. All rights reserved.


from abc import ABC
from typing import Any, ClassVar

from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.utils.feature_stage_decorator import experimental


@experimental
class FilterClauseBase(ABC, KernelBaseModel):
    """A base for all filter clauses."""

    filter_clause_type: ClassVar[str] = "FilterClauseBase"
    field_name: str
    value: Any

    def __str__(self) -> str:
        """Return a string representation of the filter clause."""
        return f"filter_clause_type='{self.filter_clause_type}' field_name='{self.field_name}' value='{self.value}'"
