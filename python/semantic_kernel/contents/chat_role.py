# Copyright (c) Microsoft. All rights reserved.
from enum import Enum


class ChatRole(str, Enum):
    """Chat role enum"""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"
