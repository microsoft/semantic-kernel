# Copyright (c) Microsoft. All rights reserved.

import logging
import urllib

from httpx import AsyncClient, HTTPStatusError, RequestError
from pydantic import ValidationError

from semantic_kernel.connectors.search_engine.connector import ConnectorBase
from semantic_kernel.connectors.search_engine.google_search_settings import GoogleSearchSettings
from semantic_kernel.exceptions import ServiceInitializationError, ServiceInvalidRequestError

logger: logging.Logger = logging.getLogger(__name__)


class GoogleConnector(ConnectorBase):
    """A search engine connector that uses the Google Custom Search API to perform a web search."""

    _settings: GoogleSearchSettings

    def __init__(
        self,
        api_key: str | None = None,
        search_engine_id: str | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
    ) -> None:
        """Initializes a new instance of the GoogleConnector class.

        Args:
            api_key (str | None): The Google Custom Search API key. If provided, will override
                the value in the env vars or .env file.
            search_engine_id (str | None): The Google search engine ID. If provided, will override
                the value in the env vars or .env file.
            env_file_path (str | None): The optional path to the .env file. If provided,
                the settings are read from this file path location.
            env_file_encoding (str | None): The optional encoding of the .env file.
        """
        try:
            self._settings = GoogleSearchSettings(
                search_api_key=api_key,
                search_engine_id=search_engine_id,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as ex:
            raise ServiceInitializationError("Failed to create Google Search settings.") from ex

        if not self._settings.search_engine_id:
            raise ServiceInitializationError("Google search engine ID cannot be null.")

    async def search(self, query: str, num_results: int = 1, offset: int = 0) -> list[str]:
        """Returns the search results of the query provided by pinging the Google Custom search API.

        Args:
            query (str): The search query.
            num_results (int): The number of search results to return. Default is 1.
            offset (int): The offset of the search results. Default is 0.

        Returns:
            list[str]: A list of search results snippets.
        """
        if not query:
            raise ServiceInvalidRequestError("query cannot be 'None' or empty.")

        if num_results <= 0:
            raise ServiceInvalidRequestError("num_results value must be greater than 0.")
        if num_results > 10:
            raise ServiceInvalidRequestError("num_results value must be less than or equal to 10.")

        if offset < 0:
            raise ServiceInvalidRequestError("offset must be greater than 0.")

        logger.info(
            f"Received request for google search with \
                params:\nquery: {query}\nnum_results: {num_results}\noffset: {offset}"
        )

        base_url = "https://www.googleapis.com/customsearch/v1"
        request_url = (
            f"{base_url}?q={urllib.parse.quote_plus(query)}"
            f"&key={self._settings.search_api_key.get_secret_value()}&cx={self._settings.search_engine_id}"
            f"&num={num_results}&start={offset}"
        )

        logger.info("Sending GET request to Google Search API.")

        try:
            async with AsyncClient(timeout=5) as client:
                response = await client.get(request_url)
                response.raise_for_status()
                data = response.json()
                logger.info("Request successful.")
                logger.info(f"API Response: {data}")
                return [x["snippet"] for x in data.get("items", [])]
        except HTTPStatusError as ex:
            logger.error(f"Failed to get search results: {ex}")
            raise ServiceInvalidRequestError("Failed to get search results.") from ex
        except RequestError as ex:
            logger.error(f"Client error occurred: {ex}")
            raise ServiceInvalidRequestError("A client error occurred while getting search results.") from ex
        except Exception as ex:
            logger.error(f"An unexpected error occurred: {ex}")
            raise ServiceInvalidRequestError("An unexpected error occurred while getting search results.") from ex
