# Copyright (c) Microsoft. All rights reserved.

import logging
import urllib

from httpx import AsyncClient, HTTPStatusError, RequestError
from pydantic import ValidationError

from semantic_kernel.connectors.search_engine.brave_connector_settings import BraveSettings
from semantic_kernel.connectors.search_engine.connector import ConnectorBase
from semantic_kernel.exceptions import ServiceInitializationError, ServiceInvalidRequestError

logger: logging.Logger = logging.getLogger(__name__)


class BraveConnector(ConnectorBase):
    """A search engine connector that uses the Brave Search API to perform a web search."""

    _settings: BraveSettings

    def __init__(
        self,
        api_key: str | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
    ) -> None:
        """Initializes a new instance of the BraveConnector class.

        Args:
            api_key (str | None): The Brave Search API key. If provided, will override
                the value in the env vars or .env file.
            custom_config (str | None): The Brave Custom Search instance's unique identifier.
                If provided, will override the value in the env vars or .env file.
            env_file_path (str | None): The optional path to the .env file. If provided,
                the settings are read from this file path location.
            env_file_encoding (str | None): The optional encoding of the .env file.
        """
        try:
            self._settings = BraveSettings.create(
                api_key=api_key,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as ex:
            raise ServiceInitializationError("Failed to create Brave settings.") from ex

    async def search(self, query: str, num_results: int = 1, offset: int = 0) -> list[str]:
        """Returns the search results of the query provided by pinging the Brave web search API."""
        if not query:
            raise ServiceInvalidRequestError("query cannot be 'None' or empty.")

        if num_results <= 0:
            raise ServiceInvalidRequestError("num_results value must be greater than 0.")
        if num_results > 20:
            raise ServiceInvalidRequestError("num_results value must be less than or equal to 20.")

        if offset < 0:
            raise ServiceInvalidRequestError("offset must be greater than 0.")
        if offset > 9:
            raise ServiceInvalidRequestError("offset must be less than 10.")

        logger.info(
            f"Received request for brave web search with \
                params:\nquery: {query}\nnum_results: {num_results}\noffset: {offset}"
        )

        base_url = "https://api.search.brave.com/res/v1/web/search"

        request_url = f"{base_url}?q={urllib.parse.quote_plus(query)}&count={num_results}&offset={offset}"

        logger.info(f"Sending GET request to {request_url}")

        if self._settings.api_key is not None:
            headers = {"X-Subscription-Token": self._settings.api_key.get_secret_value()}

        try:
            async with AsyncClient(timeout=5) as client:
                response = await client.get(request_url, headers=headers)
                response.raise_for_status()
                data = response.json()
                pages = data.get("web", {}).get("results")
                if pages:
                    return [page["description"] for page in pages]
                return []

        except HTTPStatusError as ex:
            logger.error(f"Failed to get search results: {ex}")
            raise ServiceInvalidRequestError("Failed to get search results.") from ex

        except RequestError as ex:
            logger.error(f"Client error occurred: {ex}")
            raise ServiceInvalidRequestError("A client error occurred while getting search results.") from ex

        except Exception as ex:
            logger.error(f"An unexpected error occurred: {ex}")
            raise ServiceInvalidRequestError("An unexpected error occurred while getting search results.") from ex
