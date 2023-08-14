"""Class to hold roles."""
from enum import Enum


class Role(str, Enum):
    """Enum to hold the role of the message."""

    system = "system"
    user = "user"
    assistant = "assistant"
    function = "function"
