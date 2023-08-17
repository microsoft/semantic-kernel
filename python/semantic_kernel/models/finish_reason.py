"""Class to hold finish reasons."""
from enum import Enum


class FinishReason(str, Enum):
    """Enum to hold the reason for finishing the message."""

    STOP = "stop"
    LENGTH = "length"
    FUNCTION_CALL = "function_call"
