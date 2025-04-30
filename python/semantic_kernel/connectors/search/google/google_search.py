# Copyright (c) Microsoft. All rights reserved.

import logging
from collections.abc import AsyncIterable
from typing import TYPE_CHECKING, Any
from urllib.parse import quote_plus

from httpx import AsyncClient, HTTPStatusError, RequestError
from pydantic import ValidationError

from semantic_kernel.connectors.search.google.const import CUSTOM_SEARCH_URL, QUERY_PARAMETERS
from semantic_kernel.connectors.search.google.google_search_response import GoogleSearchResponse
from semantic_kernel.connectors.search.google.google_search_result import GoogleSearchResult
from semantic_kernel.connectors.search.google.google_search_settings import GoogleSearchSettings
from semantic_kernel.data.text_search import (
    AnyTagsEqualTo,
    EqualTo,
    KernelSearchResults,
    TextSearch,
    TextSearchOptions,
    TextSearchResult,
)
from semantic_kernel.exceptions import ServiceInitializationError, ServiceInvalidRequestError
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.utils.feature_stage_decorator import experimental
from semantic_kernel.utils.telemetry.user_agent import SEMANTIC_KERNEL_USER_AGENT

if TYPE_CHECKING:
    from semantic_kernel.data.text_search import SearchOptions

logger: logging.Logger = logging.getLogger(__name__)


@experimental
class GoogleSearch(KernelBaseModel, TextSearch):
    """A search engine connector that uses the Google Search API to perform a web search."""

    settings: GoogleSearchSettings

    def __init__(
        self,
        api_key: str | None = None,
        search_engine_id: str | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
    ) -> None:
        """Initializes a new instance of the Google Search class.

        Args:
            api_key: The Google Search API key. If provided, will override
                the value in the env vars or .env file.
            search_engine_id: The Google search engine ID.
                If provided, will override the value in the env vars or .env file.
            env_file_path: The optional path to the .env file. If provided,
                the settings are read from this file path location.
            env_file_encoding: The optional encoding of the .env file.
        """
        try:
            settings = GoogleSearchSettings(
                api_key=api_key,
                engine_id=search_engine_id,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as ex:
            raise ServiceInitializationError("Failed to create Google settings.") from ex

        super().__init__(settings=settings)  # type: ignore[call-arg]

    async def search(
        self, query: str, options: "SearchOptions | None" = None, **kwargs: Any
    ) -> "KernelSearchResults[str]":
        """Search for text, returning a KernelSearchResult with a list of strings."""
        options = self._get_options(options, **kwargs)
        results = await self._inner_search(query=query, options=options)
        return KernelSearchResults(
            results=self._get_result_strings(results),
            total_count=self._get_total_count(results, options),
            metadata=self._get_metadata(results),
        )

    async def get_text_search_results(
        self, query: str, options: "SearchOptions | None" = None, **kwargs
    ) -> "KernelSearchResults[TextSearchResult]":
        """Search for text, returning a KernelSearchResult with TextSearchResults."""
        options = self._get_options(options, **kwargs)
        results = await self._inner_search(query=query, options=options)
        return KernelSearchResults(
            results=self._get_text_search_results(results),
            total_count=self._get_total_count(results, options),
            metadata=self._get_metadata(results),
        )

    async def get_search_results(
        self, query: str, options: "SearchOptions | None" = None, **kwargs
    ) -> "KernelSearchResults[GoogleSearchResult]":
        """Search for text, returning a KernelSearchResult with the results directly from the service."""
        options = self._get_options(options, **kwargs)
        results = await self._inner_search(query=query, options=options)
        return KernelSearchResults(
            results=self._get_google_search_results(results),
            total_count=self._get_total_count(results, options),
            metadata=self._get_metadata(results),
        )

    async def _get_result_strings(self, response: GoogleSearchResponse) -> AsyncIterable[str]:
        if response.items is None:
            return
        for item in response.items:
            yield item.snippet or ""

    async def _get_text_search_results(self, response: GoogleSearchResponse) -> AsyncIterable[TextSearchResult]:
        if response.items is None:
            return
        for item in response.items:
            yield TextSearchResult(
                name=item.title,
                value=item.snippet,
                link=item.link,
            )

    async def _get_google_search_results(self, response: GoogleSearchResponse) -> AsyncIterable[GoogleSearchResult]:
        if response.items is None:
            return
        for val in response.items:
            yield val

    def _get_metadata(self, response: GoogleSearchResponse) -> dict[str, Any]:
        return {
            "search_time": response.search_information.search_time if response.search_information else 0,
        }

    def _get_total_count(self, response: GoogleSearchResponse, options: TextSearchOptions) -> int | None:
        total_results = (
            None
            if not options.include_total_count
            else response.search_information.total_results or None
            if response.search_information
            else None
        )
        if total_results is not None:
            return int(total_results)
        return None

    def _get_options(self, options: "SearchOptions | None", **kwargs: Any) -> TextSearchOptions:
        if options is not None and isinstance(options, TextSearchOptions):
            return options
        try:
            return TextSearchOptions(**kwargs)
        except ValidationError:
            return TextSearchOptions()

    async def _inner_search(self, query: str, options: TextSearchOptions) -> GoogleSearchResponse:
        self._validate_options(options)

        logger.info(
            f"Received request for google web search with \
                params:\nnum_results: {options.top}\noffset: {options.skip}"
        )

        full_url = f"{CUSTOM_SEARCH_URL}{self._build_query(query, options)}"
        headers = {"user_agent": SEMANTIC_KERNEL_USER_AGENT}
        try:
            async with AsyncClient(timeout=5) as client:
                response = await client.get(full_url, headers=headers)
                response.raise_for_status()
                return GoogleSearchResponse.model_validate_json(response.text)
        except HTTPStatusError as ex:
            logger.error(f"Failed to get search results: {ex}")
            raise ServiceInvalidRequestError("Failed to get search results.") from ex
        except RequestError as ex:
            logger.error(f"Client error occurred: {ex}")
            raise ServiceInvalidRequestError("A client error occurred while getting search results.") from ex
        except Exception as ex:
            logger.error(f"An unexpected error occurred: {ex}")
            raise ServiceInvalidRequestError("An unexpected error occurred while getting search results.") from ex

    def _validate_options(self, options: TextSearchOptions) -> None:
        if options.top > 10:
            raise ServiceInvalidRequestError("count value must be less than or equal to 10.")

    def _build_query(self, query: str, options: TextSearchOptions) -> str:
        params = {
            "key": self.settings.api_key.get_secret_value(),
            "cx": self.settings.engine_id,
            "num": options.top,
            "start": options.skip,
        }
        if options.filter:
            for filter in options.filter.filters:
                if isinstance(filter, EqualTo):
                    if filter.field_name in QUERY_PARAMETERS:
                        params[filter.field_name] = quote_plus(filter.value)
                elif isinstance(filter, AnyTagsEqualTo):
                    logger.debug("AnyTagEqualTo filter is not supported by Google Search API.")
        return f"?q={quote_plus(query)}&{'&'.join(f'{k}={v}' for k, v in params.items())}"
