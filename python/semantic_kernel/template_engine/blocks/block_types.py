# Copyright (c) Microsoft. All rights reserved.

from enum import Enum


class BlockTypes(Enum):
    Undefined = 0
    Text = 1
    Code = 2
    Variable = 3
