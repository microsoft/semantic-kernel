# Copyright (c) Microsoft. All rights reserved.
from enum import Enum


class AuthorRole(str, Enum):
    """Author role enum."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"
    DEVELOPER = "developer"
