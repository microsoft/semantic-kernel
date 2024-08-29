# Copyright (c) Microsoft. All rights reserved.

from enum import Enum


class FilterClauseType(str, Enum):
    """Types of filter clauses for search queries."""

    EQUALITY = "equality"
    TAG_LIST_CONTAINS = "tag_list_contains"
