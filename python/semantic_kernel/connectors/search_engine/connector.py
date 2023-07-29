# Copyright (c) Microsoft. All rights reserved.

from typing import List


class ConnectorBase:
    """
    Base class for search engine connectors
    """

    def search_async(self, query: str, num_results: str, offset: str) -> List[str]:
        pass
