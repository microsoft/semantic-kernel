# Copyright (c) Microsoft. All rights reserved.

from enum import Enum
from typing import Final

DEFAULT_COUNT: Final[int] = 5


class FilterClauseType(str, Enum):
    """Types of filter clauses for search queries."""

    EQUALITY = "equality"
    TAG_LIST_CONTAINS = "tag_list_contains"
