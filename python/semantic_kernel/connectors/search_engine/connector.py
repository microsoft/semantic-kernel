# Copyright (c) Microsoft. All rights reserved.

from abc import ABC, abstractmethod


class ConnectorBase(ABC):
    """Base class for search engine connectors."""

    @abstractmethod
    async def search(
        self, query: str, num_results: int = 1, offset: int = 0
    ) -> list[str]:
        """Returns the search results of the query provided by pinging the search engine API."""
