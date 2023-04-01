# Copyright (c) Microsoft. All rights reserved.

from enum import Enum, auto


class BlockTypes(Enum):
    UNDEFINED = auto()
    TEXT = auto()
    CODE = auto()
    VARIABLE = auto()
    VALUE = auto()
    FUNCTION_ID = auto()
