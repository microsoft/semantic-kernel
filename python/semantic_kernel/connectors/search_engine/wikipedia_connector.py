# Copyright (c) Microsoft. All rights reserved.

from logging import Logger
from typing import List, Optional

from semantic_kernel.connectors.search_engine.connector import ConnectorBase
from semantic_kernel.utils.null_logger import NullLogger

class WikipediaConnector(ConnectorBase):
    """
    A search engine connector using the MediaWiki Action API to perform a Wikipedia search
    """

    _logger: Logger

    def __init__(self, logger: Optional[Logger] = None) -> None:
        self._logger = logger or NullLogger()

    async def search_async(self, query: str, num_results: str, offset: str) -> List[str]:
        pass
