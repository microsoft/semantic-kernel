# Copyright (c) Microsoft. All rights reserved.
from __future__ import annotations

from enum import Enum


class ChatRole(str, Enum):
    """Chat role enum"""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"
