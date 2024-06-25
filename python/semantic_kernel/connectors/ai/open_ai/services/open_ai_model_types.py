# Copyright (c) Microsoft. All rights reserved.

from enum import Enum


class OpenAIModelTypes(Enum):
    """OpenAI model types, can be text, chat or embedding."""

    TEXT = "text"
    CHAT = "chat"
    EMBEDDING = "embedding"
