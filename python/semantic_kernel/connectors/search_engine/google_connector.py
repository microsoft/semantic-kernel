from typing import Optional, List
from logging import Logger
from semantic_kernel.utils.null_logger import NullLogger
from semantic_kernel.connectors.search_engine.connector import ConnectorBase


class GoogleConnector(ConnectorBase):
    """
    A search engine connector that uses the Google Custom Search API to perform a web search.
    """

    _api_key: str
    _search_engine_id: str
    _logger: Logger

    def __init__(
        self, api_key: str, search_engine_id: str, logger: Optional[Logger] = None
    ) -> None:
        self._api_key = api_key
        self._search_engine_id = search_engine_id
        self._logger = logger if logger else NullLogger()

        if not self._api_key:
            raise ValueError("Google Custom Search API key cannot be null.")

        if not self._search_engine_id:
            raise ValueError("Google search engine ID cannot be null.")

    async def search_async(
        self, query: str, num_results: str, offset: str
    ) -> List[str]:
        return super().search_async(query, num_results, offset)
