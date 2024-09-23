# Copyright (c) Microsoft. All rights reserved.

from enum import Enum


class FilterClauseType(str, Enum):
    """Types of filter clauses for search queries."""

    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    ANY_TAG_EQUAL_TO = "any_tag_equal_to"
