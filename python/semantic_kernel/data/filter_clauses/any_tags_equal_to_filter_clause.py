# Copyright (c) Microsoft. All rights reserved.


from typing import ClassVar

from semantic_kernel.data.filter_clauses.filter_clause_base import FilterClauseBase
from semantic_kernel.utils.feature_stage_decorator import experimental


@experimental
class AnyTagsEqualTo(FilterClauseBase):
    """A filter clause for a any tags equals comparison.

    Args:
        field_name: The name of the field containing the list of tags.
        value: The value to compare against the list of tags.
    """

    filter_clause_type: ClassVar[str] = "any_tags_equal_to"
