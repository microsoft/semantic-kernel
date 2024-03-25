# Copyright (c) Microsoft. All rights reserved.
from __future__ import annotations

from enum import Enum, auto


class BlockTypes(Enum):
    UNDEFINED = auto()
    TEXT = auto()
    CODE = auto()
    VARIABLE = auto()
    VALUE = auto()
    FUNCTION_ID = auto()
    NAMED_ARG = auto()
