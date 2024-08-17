# Copyright (c) Microsoft. All rights reserved.
from enum import Enum


class Symbols(str, Enum):
    """Symbols used in the template engine."""

    BLOCK_STARTER = "{"
    BLOCK_ENDER = "}"

    VAR_PREFIX = "$"

    DBL_QUOTE = '"'
    SGL_QUOTE = "'"
    ESCAPE_CHAR = "\\"

    SPACE = " "
    TAB = "\t"
    NEW_LINE = "\n"
    CARRIAGE_RETURN = "\r"

    NAMED_ARG_BLOCK_SEPARATOR = "="
