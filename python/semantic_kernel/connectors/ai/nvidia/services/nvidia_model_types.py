# Copyright (c) Microsoft. All rights reserved.

from enum import Enum


class NvidiaModelTypes(Enum):
    """Nvidia model types, can be text, chat or embedding."""

    TEXT = "text"
    CHAT = "chat"
    EMBEDDING = "embedding"
    TEXT_TO_IMAGE = "text-to-image"
