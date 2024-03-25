# Copyright (c) Microsoft. All rights reserved.
from __future__ import annotations

from abc import ABC, abstractmethod


class ConnectorBase(ABC):
    """
    Base class for search engine connectors
    """

    @abstractmethod
    async def search(self, query: str, num_results: int = 1, offset: int = 0) -> list[str]:
        pass
