# Copyright (c) Microsoft. All rights reserved.

import logging
import urllib

import aiohttp

from semantic_kernel.connectors.search_engine.bing_connector_settings import BingSettings
from semantic_kernel.connectors.search_engine.connector import ConnectorBase
from semantic_kernel.exceptions import ServiceInvalidRequestError

logger: logging.Logger = logging.getLogger(__name__)


class BingConnector(ConnectorBase):
    """A search engine connector that uses the Bing Search API to perform a web search."""

    _settings: BingSettings

    def __init__(
        self,
        api_key: str | None = None,
        custom_config: str | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
    ) -> None:
        """Initializes a new instance of the BingConnector class.

        Args:
            api_key (str | None): The Bing Search API key. If provided, will override
                the value in the env vars or .env file.
            custom_config (str | None): The Bing Custom Search instance's unique identifier.
                If provided, will override the value in the env vars or .env file.
            env_file_path (str | None): The optional path to the .env file. If provided,
                the settings are read from this file path location.
            env_file_encoding (str | None): The optional encoding of the .env file.
        """
        self._settings = BingSettings.create(
            api_key=api_key,
            custom_config=custom_config,
            env_file_path=env_file_path,
            env_file_encoding=env_file_encoding,
        )

    async def search(self, query: str, num_results: int = 1, offset: int = 0) -> list[str]:
        """Returns the search results of the query provided by pinging the Bing web search API."""
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

        _base_url = (
            "https://api.bing.microsoft.com/v7.0/custom/search"
            if self._settings.custom_config
            else "https://api.bing.microsoft.com/v7.0/search"
        )
        _request_url = (
            f"{_base_url}?q={urllib.parse.quote_plus(query)}&count={num_results}&offset={offset}"
            + (
                f"&customConfig={self._settings.custom_config}"
                if self._settings.custom_config
                else ""
            )
        )

        logger.info(f"Sending GET request to {_request_url}")

        headers = {"Ocp-Apim-Subscription-Key": self._settings.api_key.get_secret_value()}

        async with (
            aiohttp.ClientSession() as session,
            session.get(_request_url, headers=headers, raise_for_status=True) as response,
        ):
            if response.status == 200:
                data = await response.json()
                pages = data.get("webPages", {}).get("value")
                if pages:
                    return list(map(lambda x: x["snippet"], pages)) or []
                return None
            return []
