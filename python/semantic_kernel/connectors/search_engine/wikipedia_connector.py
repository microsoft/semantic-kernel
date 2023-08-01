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
        """
        Create an instance of WikipediaConnector

        Arguments:
            logger {Optional[Logger]} -- Logger, defaults to None
        """
        self._logger = logger or NullLogger()

    async def search_async(
        self, query: str, num_results: int = 1, offset: int = 0
    ) -> List[str]:
        """
        Returns search results of the query from the Wikipedia API.
        Returns `num_results` results and ignores the first `offset`.

        Arguments:
            query {str} -- Search query
            num_results {int} -- Number of results to return
            offset {int} -- Number of results to ignore

        Returns:
            List[str] -- List of search results
        """
        if not query:
            raise ValueError("Query cannot be None or empty")

        pass
