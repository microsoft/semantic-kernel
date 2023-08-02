# Copyright (c) Microsoft. All rights reserved.

import re
from logging import Logger
from typing import List, Optional, Tuple

import aiohttp

from semantic_kernel.connectors.search_engine.connector import ConnectorBase
from semantic_kernel.utils.null_logger import NullLogger

SNIPPET_PATTERN = r"<span[^>]*>(.*?)</span>"


class WikipediaConnector(ConnectorBase):
    """
    A search engine connector using the MediaWiki Action API to perform a Wikipedia search
    """

    _endpoint: str
    _logger: Logger

    def __init__(
        self,
        endpoint_url: str = "https://en.wikipedia.org/w/api.php",
        logger: Optional[Logger] = None,
    ) -> None:
        """
        Create an instance of WikipediaConnector

        Arguments:
            endpoint_url {str} -- URL to ping, defaults to the English Wikipedia endpoint
            logger {Optional[Logger]} -- Logger, defaults to None
        """
        self._endpoint = endpoint_url
        self._logger = logger or NullLogger()

    async def search_async(
        self, query: str, num_results: str = "1", offset: str = "0"
    ) -> List[Tuple[str, str]]:
        """
        Returns search results of the query from the Wikipedia API.
        Returns `num_results` results and ignores the first `offset`.

        Arguments:
            query {str} -- Search query
            num_results {int} -- Number of results to return
            offset {int} -- Number of results to ignore

        Returns:
            List[Tuple[str, str]] -- List of search results formatted as the title of the Wikipedia article
                and a brief snippet of its content
        """
        if not query:
            raise ValueError("Query cannot be None or empty")

        if not num_results:
            num_results = 1
        if not offset:
            offset = 0

        num_results = int(num_results)
        offset = int(offset)

        if num_results <= 0:
            raise ValueError("num_results value must be greater than 0.")
        if num_results > 500:
            raise ValueError("num_results value must be less than or equal to 500.")

        if offset < 0:
            raise ValueError("offset must be greater than 0.")

        self._logger.info(
            f"Received request for Wikiepdia search with \
                params:\nquery: {query}\nnum_results: {num_results}\noffset: {offset}"
        )

        parameters = {
            "action": "query",
            "format": "json",
            "list": "search",
            "srsearch": query,
            "srlimit": num_results,
            "sroffset": offset,
            "srenablerewrites": 1,  # Enable rewriting of query to help with mistakes, typos, etc.
            "srprop": "snippet",
        }

        self._logger.info("Sending GET request to Wikipedia API.")

        async with aiohttp.ClientSession() as session:
            async with session.get(
                self._endpoint, params=parameters, raise_for_status=True
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self._logger.info("Request successful.")
                    self._logger.info(f"API Response: {data}")

                    all_search_results = data["query"]["search"]
                    result = []
                    for sr in all_search_results:
                        article_title = sr["title"]
                        # Remove span tags that come from the search
                        article_snippet = re.sub(SNIPPET_PATTERN, r"\1", sr["snippet"])
                        result.append((article_title, article_snippet))

                    return result
                else:
                    self._logger.error(
                        f"Request to Wikipedia API failed with status code: {response.status}."
                    )
                    return []
