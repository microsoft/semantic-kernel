# Copyright (c) Microsoft. All rights reserved.

from enum import Enum


class MiniMaxModelTypes(Enum):
    """MiniMax model types, can be chat or embedding."""

    CHAT = "chat"
    EMBEDDING = "embedding"
