"""Class to hold finish reasons."""
from enum import Enum


class FinishReasonEnum(str, Enum):
    """Enum to hold the reason for finishing the message."""

    stop = "stop"
    length = "length"
    function_call = "function_call"
