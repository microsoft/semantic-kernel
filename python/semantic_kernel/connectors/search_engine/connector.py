# Copyright (c) Microsoft. All rights reserved.

from abc import ABC, abstractmethod
from typing import List


class ConnectorBase(ABC):
    """
    Base class for search engine connectors
    """

    @abstractmethod
    async def search(self, query: str, num_results: int = 1, offset: int = 0) -> List[str]:
        pass
