# Copyright (c) Microsoft. All rights reserved.

import logging
from html import escape
from typing import Any

from azure.cognitiveservices.search.websearch import WebSearchClient
from azure.cognitiveservices.search.websearch.models import ErrorResponseException
from msrest.authentication import CognitiveServicesCredentials
from pydantic import ValidationError

from semantic_kernel.connectors.search.bing.bing_search_response import BingSearchResponse
from semantic_kernel.connectors.search.bing.bing_web_page import BingWebPage
from semantic_kernel.connectors.search.bing.const import (
    DEFAULT_CUSTOM_URL,
    DEFAULT_URL,
    QUERY_ADVANCED_SEARCH_KEYWORDS,
    QUERY_PARAMETERS,
)
from semantic_kernel.connectors.search_engine.bing_connector_settings import BingSettings
from semantic_kernel.exceptions import ServiceInitializationError, ServiceInvalidRequestError
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.search.const import FilterClauseType
from semantic_kernel.search.kernel_search_result import KernelSearchResult
from semantic_kernel.search.text_search import TextSearch
from semantic_kernel.search.text_search_options import TextSearchOptions
from semantic_kernel.search.text_search_result import TextSearchResult
from semantic_kernel.utils.telemetry.user_agent import SEMANTIC_KERNEL_USER_AGENT

logger: logging.Logger = logging.getLogger(__name__)


class BingSearch(KernelBaseModel, TextSearch):
    """A search engine connector that uses the Bing Search API to perform a web search."""

    client: WebSearchClient

    def __init__(
        self,
        api_key: str | None = None,
        custom_config: str | None = None,
        client: WebSearchClient | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
    ) -> None:
        """Initializes a new instance of the BingConnector class.

        Args:
            api_key: The Bing Search API key. If provided, will override
                the value in the env vars or .env file.
            custom_config: The Bing Custom Search instance's unique identifier.
                If provided, will override the value in the env vars or .env file.
            client: Provide a client to use for the Bing Search API.
            env_file_path: The optional path to the .env file. If provided,
                the settings are read from this file path location.
            env_file_encoding: The optional encoding of the .env file.
        """
        if client:
            super().__init__(client=client)
        try:
            settings = BingSettings.create(
                api_key=api_key,
                custom_config=custom_config,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as ex:
            raise ServiceInitializationError("Failed to create Bing settings.") from ex
        client = WebSearchClient(
            endpoint=f"{DEFAULT_CUSTOM_URL}&customConfig={settings.custom_config}"
            if settings.custom_config
            else DEFAULT_URL,
            credentials=CognitiveServicesCredentials(settings.api_key.get_secret_value()),
        )
        super().__init__(client=client)

    async def search(self, options: TextSearchOptions | None = None, **kwargs: Any) -> "KernelSearchResult[str]":
        """Search for text, returning a KernelSearchResult with a list of strings."""
        options = self._get_options(options, **kwargs)
        results = await self._inner_search(options=options)
        return KernelSearchResult(
            results=self._get_result_strings(results),
            total_count=self._get_total_count(results, options),
            metadata=self._get_metadata(results),
        )

    async def get_text_search_result(
        self, options: TextSearchOptions | None = None, **kwargs
    ) -> "KernelSearchResult[TextSearchResult]":
        """Search for text, returning a KernelSearchResult with TextSearchResults."""
        options = self._get_options(options, **kwargs)
        results = await self._inner_search(options=options)
        return KernelSearchResult(
            results=self._get_text_search_results(results),
            total_count=self._get_total_count(results, options),
            metadata=self._get_metadata(results),
        )

    async def get_search_result(
        self, options: TextSearchOptions | None = None, **kwargs
    ) -> "KernelSearchResult[BingWebPage]":
        """Search for text, returning a KernelSearchResult with the results directly from the service."""
        options = self._get_options(options, **kwargs)
        results = await self._inner_search(options=options)
        return KernelSearchResult(
            results=self._get_bing_web_pages(results),
            total_count=self._get_total_count(results, options),
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

    def _get_total_count(self, response: BingSearchResponse, options: TextSearchOptions) -> int | None:
        return (
            None
            if not options.include_total_count
            else response.web_pages.total_estimated_matches or None
            if response.web_pages
            else None
        )

    def _get_options(self, options: TextSearchOptions | None, **kwargs: Any) -> TextSearchOptions:
        if options is not None:
            return options
        try:
            return TextSearchOptions(**kwargs)
        except ValidationError:
            return TextSearchOptions()

    async def _inner_search(self, options: TextSearchOptions) -> BingSearchResponse:
        self._validate_options(options)
        dict_options = self._update_options(options)
        try:
            response = self.client.web.search(**dict_options)
            return BingSearchResponse.model_validate_json(response.text)
        except ErrorResponseException as ex:
            logger.error(f"Failed to get search results: {ex}")
            raise ServiceInvalidRequestError("Failed to get search results.") from ex
        except Exception as ex:
            logger.error(f"An unexpected error occurred: {ex}")
            raise ServiceInvalidRequestError("An unexpected error occurred while getting search results.") from ex

    def _validate_options(self, options: TextSearchOptions) -> None:
        if options.count >= 50:
            raise ServiceInvalidRequestError("count value must be less than 50.")
        if not options.query:
            raise ServiceInvalidRequestError("query cannot be 'None' or empty.")

    def _get_url(self) -> str:
        if not self.settings.custom_config:
            return DEFAULT_URL
        return f"{DEFAULT_CUSTOM_URL}&customConfig={self.settings.custom_config}"

    def _update_options(self, options: TextSearchOptions) -> dict[str, Any]:
        params = {"count": options.count, "offset": options.offset}
        extra_query_params = []

        for filter in options.search_filters:
            if filter.field_name in QUERY_PARAMETERS and filter.clause_type == FilterClauseType.EQUALITY:
                params[filter.field_name] = escape(filter.value)
            if filter.field_name in QUERY_ADVANCED_SEARCH_KEYWORDS and filter.clause_type == FilterClauseType.EQUALITY:
                extra_query_params.append(f"{filter.field_name}:{filter.value}")
            if filter.clause_type == FilterClauseType.TAG_LIST_CONTAINS:
                logger.debug("Tag list contains filter is not supported by Bing Search API.")
        params["query"] = f"{options.query}+{' '.join(extra_query_params)}".strip()
        if "user_agent" not in params:
            params["user_agent"] = SEMANTIC_KERNEL_USER_AGENT
        return params
