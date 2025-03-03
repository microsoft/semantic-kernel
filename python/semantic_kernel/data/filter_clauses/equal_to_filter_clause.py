# Copyright (c) Microsoft. All rights reserved.

from typing import ClassVar

from semantic_kernel.data.filter_clauses.filter_clause_base import FilterClauseBase
from semantic_kernel.utils.feature_stage_decorator import experimental


@experimental
class EqualTo(FilterClauseBase):
    """A filter clause for an equals comparison.

    Args:
        field_name: The name of the field to compare.
        value: The value to compare against the field.

    """

    filter_clause_type: ClassVar[str] = "equal_to"
