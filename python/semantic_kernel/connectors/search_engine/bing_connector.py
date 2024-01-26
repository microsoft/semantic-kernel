# Copyright (c) Microsoft. All rights reserved.

import logging
import urllib
from typing import List

import aiohttp

from semantic_kernel.connectors.search_engine.connector import ConnectorBase

logger: logging.Logger = logging.getLogger(__name__)


class BingConnector(ConnectorBase):
    """
    A search engine connector that uses the Bing Search API to perform a web search
    """

    _api_key: str

    def __init__(self, api_key: str, **kwargs) -> None:
        if kwargs.get("logger"):
            logger.warning("The `logger` parameter is deprecated. Please use the `logging` module instead.")
        self._api_key = api_key

        if not self._api_key:
            raise ValueError("Bing API key cannot be null. Please set environment variable BING_API_KEY.")

    async def search(self, query: str, num_results: str, offset: str) -> List[str]:
        """
        Returns the search results of the query provided by pinging the Bing web search API.
        Returns `num_results` results and ignores the first `offset`.

        :param query: search query
        :param num_results: the number of search results to return
        :param offset: the number of search results to ignore
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

        logger.info(
            f"Received request for bing web search with \
                params:\nquery: {query}\nnum_results: {num_results}\noffset: {offset}"
        )

        _base_url = "https://api.bing.microsoft.com/v7.0/search"
        _request_url = f"{_base_url}?q={urllib.parse.quote_plus(query)}&count={num_results}&offset={offset}"

        logger.info(f"Sending GET request to {_request_url}")

        headers = {"Ocp-Apim-Subscription-Key": self._api_key}

        async with aiohttp.ClientSession() as session:
            async with session.get(_request_url, headers=headers, raise_for_status=True) as response:
                if response.status == 200:
                    data = await response.json()
                    pages = data["webPages"]["value"]
                    logger.info(pages)
                    result = list(map(lambda x: x["snippet"], pages))
                    logger.info(result)
                    return result
                else:
                    return []
