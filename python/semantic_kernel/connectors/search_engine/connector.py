# Copyright (c) Microsoft. All rights reserved.

from abc import ABC, abstractmethod
from typing import List


class ConnectorBase(ABC):
    """
    Base class for search engine connectors
    """

    @abstractmethod
    async def search(self, query: str, num_results: str, offset: str) -> List[str]:
        pass
