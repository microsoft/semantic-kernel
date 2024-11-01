# Copyright (c) Microsoft. All rights reserved.

from enum import Enum, auto


class BlockTypes(Enum):
    """Block types."""

    UNDEFINED = auto()
    TEXT = auto()
    CODE = auto()
    VARIABLE = auto()
    VALUE = auto()
    FUNCTION_ID = auto()
    NAMED_ARG = auto()
