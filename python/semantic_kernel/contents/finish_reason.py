# Copyright (c) Microsoft. All rights reserved.
from enum import Enum


class FinishReason(str, Enum):
    """Finish Reason enum."""

    STOP = "stop"
    LENGTH = "length"
    CONTENT_FILTER = "content_filter"
    TOOL_CALLS = "tool_calls"
    FUNCTION_CALL = "function_call"
