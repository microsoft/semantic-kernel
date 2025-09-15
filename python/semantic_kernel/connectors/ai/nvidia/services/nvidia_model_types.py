# Copyright (c) Microsoft. All rights reserved.

from enum import Enum


class NvidiaModelTypes(Enum):
    """Nvidia model types, can be text, chat or embedding."""

    EMBEDDING = "embedding"
