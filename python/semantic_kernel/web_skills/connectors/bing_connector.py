import urllib
import aiohttp
from logging import Logger
from typing import Optional, List
from semantic_kernel.web_skills.connectors import Connector
from semantic_kernel.utils.null_logger import NullLogger


class BingConnector(ConnectorBase):
    """
    A search engine connector that uses the Bing Search API to perform a web search
    """

    _api_key: str

    def __init__(self, api_key: str, logger: Optional[Logger] = None) -> None:
        self._api_key = api_key
        self._logger = logger if logger else NullLogger()

    async def search_async(self, query: str, count: str, offset: str) -> List[str]:
        """
        Returns the search results of the query provided by pinging the Bing web search API.
        Returns `num_results` results and ignores the first `offset`.

        :param query: search query
        :param context: contains the context of count and offset parameters
        :return: list of search results
        """
        if not query:
            raise ValueError("query cannot be 'None' or empty.")

        if not num_results:
            num_results = 1
        if not offset:
            offset = 0

        num_results = int(num_results)
        offset = int(offset)

        if num_results <= 0:
            raise ValueError("num_results value must be greater than 0.")
        if num_results >= 50:
            raise ValueError("num_results value must be less than 50.")

        if offset < 0:
            raise ValueError("offset must be greater than 0.")

        self._logger.info(
            f"Received request for bing web search with params:\nquery: {query}\ncount: {count}\noffset: {offset}"
        )

        _base_url = "https://api.bing.microsoft.com/v7.0/search"
        _request_url = f"{_base_url}?q={urllib.parse.quote_plus(query)}&count={num_results}&offset={offset}"

        self._logger.info(f"Sending GET request to {_request_url}")

        headers = {"Ocp-Apim-Subscription-Key": self._api_key}

        async with aiohttp.ClientSession() as session:
            async with session.get(
                _request_url, headers=headers, raise_for_status=True
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    pages = data["webPages"]["value"]
                    self._logger.info(pages)
                    result = list(map(lambda x: x["snippet"], pages))
                    self._logger.info(result)
                    return result
                else:
                    return []
