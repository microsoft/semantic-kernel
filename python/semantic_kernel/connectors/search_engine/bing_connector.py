# Copyright (c) Microsoft. All rights reserved.

import logging
import urllib
from typing import List

import aiohttp
from pydantic import ValidationError

from semantic_kernel.connectors.search_engine.bing_connector_settings import BingSettings
from semantic_kernel.connectors.search_engine.connector import ConnectorBase
from semantic_kernel.exceptions import ServiceInitializationError, ServiceInvalidRequestError

logger: logging.Logger = logging.getLogger(__name__)


class BingConnector(ConnectorBase):
    """
    A search engine connector that uses the Bing Search API to perform a web search
    """

    _api_key: str

    def __init__(self, use_env_settings_file: bool = False) -> None:
        try:
            bing_settings = BingSettings(use_env_settings_file=use_env_settings_file)
        except ValidationError as e:
            logger.error(f"Error loading Bing settings: {e}. The API key cannot be null.")
            raise ServiceInitializationError("Error loading Bing settings. The API key cannot be null.") from e
        self._api_key = bing_settings.api_key.get_secret_value()

    async def search(self, query: str, num_results: int = 1, offset: int = 0) -> List[str]:
        """
        Returns the search results of the query provided by pinging the Bing web search API.
        Returns `num_results` results and ignores the first `offset`.

        :param query: search query
        :param num_results: the number of search results to return
        :param offset: the number of search results to ignore
        :return: list of search results
        """
        if not query:
            raise ServiceInvalidRequestError("query cannot be 'None' or empty.")

        if num_results <= 0:
            raise ServiceInvalidRequestError("num_results value must be greater than 0.")
        if num_results >= 50:
            raise ServiceInvalidRequestError("num_results value must be less than 50.")

        if offset < 0:
            raise ServiceInvalidRequestError("offset must be greater than 0.")

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
                    pages = data.get("webPages", {}).get("value")
                    if pages:
                        return list(map(lambda x: x["snippet"], pages)) or []
                else:
                    return []
