# Copyright (c) Microsoft. All rights reserved.

from enum import Enum
from typing import Final

DEFAULT_COUNT: Final[int] = 5
DEFAULT_DESCRIPTION: Final[str] = (
    "Perform a search for content related to the specified query and return string results"
)


class FilterClauseType(str, Enum):
    """Types of filter clauses for search queries."""

    EQUALITY = "equality"
    TAG_LIST_CONTAINS = "tag_list_contains"
    DIRECT = "direct"
    PROMPT = "prompt"
