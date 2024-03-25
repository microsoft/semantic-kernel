# Copyright (c) Microsoft. All rights reserved.
from __future__ import annotations

from enum import Enum


class OpenAIModelTypes(Enum):
    """OpenAI model types, can be text, chat or embedding."""

    TEXT = "text"
    CHAT = "chat"
    EMBEDDING = "embedding"
