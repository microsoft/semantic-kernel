# Copyright (c) Microsoft. All rights reserved.

import logging
import urllib
from typing import Any

from httpx import AsyncClient, HTTPStatusError, RequestError
from pydantic import ValidationError

from semantic_kernel.connectors.search.bing.bing_search_response import BingSearchResponse
from semantic_kernel.connectors.search.bing.bing_web_page import BingWebPage
from semantic_kernel.connectors.search_engine.bing_connector_settings import BingSettings
from semantic_kernel.exceptions import ServiceInitializationError, ServiceInvalidRequestError
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.search.kernel_search_result import KernelSearchResult
from semantic_kernel.search.text_search_result import TextSearchResult

logger: logging.Logger = logging.getLogger(__name__)


class BingSearch(KernelBaseModel):
    """A search engine connector that uses the Bing Search API to perform a web search."""

    settings: BingSettings

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
        try:
            settings = BingSettings.create(
                api_key=api_key,
                custom_config=custom_config,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as ex:
            raise ServiceInitializationError("Failed to create Bing settings.") from ex
        super().__init__(settings=settings)

    async def search(
        self, query: str, num_results: int = 1, offset: int = 0, **kwargs: Any
    ) -> "KernelSearchResult[str]":
        """Search for text, returning a KernelSearchResult with a list of strings."""
        include_total_count = kwargs.get("include_total_count", True)
        results = await self._inner_search(query, num_results=num_results, offset=offset)
        return KernelSearchResult(
            results=self._get_result_strings(results),
            total_count=None
            if not include_total_count
            else results.web_pages.total_estimated_matches or None
            if results.web_pages
            else None,
            metadata=self._get_metadata(results),
        )

    async def get_text_search_result(
        self, query: str, num_results: int = 1, offset: int = 0, **kwargs
    ) -> "KernelSearchResult[TextSearchResult]":
        """Search for text, returning a KernelSearchResult with TextSearchResults."""
        include_total_count = kwargs.get("include_total_count", True)
        results = await self._inner_search(query, num_results=num_results, offset=offset)
        return KernelSearchResult(
            results=self._get_text_search_results(results),
            total_count=None
            if not include_total_count
            else results.web_pages.total_estimated_matches or None
            if results.web_pages
            else None,
            metadata=self._get_metadata(results),
        )

    async def get_search_result(
        self, query: str, num_results: int = 1, offset: int = 0, **kwargs
    ) -> "KernelSearchResult[BingWebPage]":
        """Search for text, returning a KernelSearchResult with the results directly from the service."""
        include_total_count = kwargs.get("include_total_count", True)
        results = await self._inner_search(query, num_results=num_results, offset=offset)
        return KernelSearchResult(
            results=self._get_bing_web_pages(results),
            total_count=None
            if not include_total_count
            else results.web_pages.total_estimated_matches or None
            if results.web_pages
            else None,
            metadata=self._get_metadata(results),
        )

    def _get_result_strings(self, response: BingSearchResponse) -> list[str]:
        if response.web_pages is None:
            return []
        return [web_page.snippet for web_page in response.web_pages.value if web_page.snippet]

    def _get_text_search_results(self, response: BingSearchResponse) -> list[TextSearchResult]:
        if response.web_pages is None:
            return []
        return [
            TextSearchResult(
                name=web_page.name,
                value=web_page.snippet,
                link=web_page.url,
            )
            for web_page in response.web_pages.value
        ]

    def _get_bing_web_pages(self, response: BingSearchResponse) -> list[BingWebPage]:
        if response.web_pages is None:
            return []
        return response.web_pages.value

    def _get_metadata(self, response: BingSearchResponse) -> dict[str, Any]:
        return {
            "altered_query": response.query_context.get("alteredQuery"),
        }

    async def _inner_search(self, query: str, num_results: int, offset: int) -> BingSearchResponse:
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

        base_url = (
            "https://api.bing.microsoft.com/v7.0/custom/search"
            if self.settings.custom_config
            else "https://api.bing.microsoft.com/v7.0/search"
        )
        request_url = f"{base_url}?q={urllib.parse.quote_plus(query)}&count={num_results}&offset={offset}" + (
            f"&customConfig={self.settings.custom_config}" if self.settings.custom_config else ""
        )

        logger.info(f"Sending GET request to {request_url}")

        if self.settings.api_key is not None:
            headers = {"Ocp-Apim-Subscription-Key": self.settings.api_key.get_secret_value()}

        try:
            async with AsyncClient() as client:
                response = await client.get(request_url, headers=headers)
                response.raise_for_status()
                return BingSearchResponse.model_validate_json(response.text)
        except HTTPStatusError as ex:
            logger.error(f"Failed to get search results: {ex}")
            raise ServiceInvalidRequestError("Failed to get search results.") from ex
        except RequestError as ex:
            logger.error(f"Client error occurred: {ex}")
            raise ServiceInvalidRequestError("A client error occurred while getting search results.") from ex
        except Exception as ex:
            logger.error(f"An unexpected error occurred: {ex}")
            raise ServiceInvalidRequestError("An unexpected error occurred while getting search results.") from ex
