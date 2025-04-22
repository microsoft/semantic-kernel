# Copyright (c) Microsoft. All rights reserved.

import logging
from collections.abc import AsyncIterable
from html import escape
from typing import TYPE_CHECKING, Any, ClassVar, Final

from httpx import AsyncClient, HTTPStatusError, RequestError
from pydantic import Field, SecretStr, ValidationError

from semantic_kernel.data.text_search import (
    AnyTagsEqualTo,
    EqualTo,
    KernelSearchResults,
    SearchFilter,
    TextSearch,
    TextSearchOptions,
    TextSearchResult,
)
from semantic_kernel.exceptions import ServiceInitializationError, ServiceInvalidRequestError
from semantic_kernel.kernel_pydantic import KernelBaseModel, KernelBaseSettings
from semantic_kernel.utils.feature_stage_decorator import experimental
from semantic_kernel.utils.telemetry.user_agent import SEMANTIC_KERNEL_USER_AGENT

if TYPE_CHECKING:
    from semantic_kernel.data.text_search import SearchOptions

logger: logging.Logger = logging.getLogger(__name__)

# region Constants
DEFAULT_URL: Final[str] = "https://api.bing.microsoft.com/v7.0/search"
DEFAULT_CUSTOM_URL: Final[str] = "https://api.bing.microsoft.com/"
QUERY_PARAMETERS: Final[list[str]] = [
    "answerCount",
    "cc",
    "freshness",
    "mkt",
    "promote",
    "responseFilter",
    "safeSearch",
    "setLang",
    "textDecorations",
    "textFormat",
]
QUERY_ADVANCED_SEARCH_KEYWORDS: Final[list[str]] = [
    "site",
    "contains",
    "ext",
    "filetype",
    "inanchor",
    "inbody",
    "intitle",
    "ip",
    "language",
    "loc",
    "location",
    "prefer",
    "feed",
    "hasfeed",
    "url",
]


# endregion Constants


# region BingSettings
class BingSettings(KernelBaseSettings):
    """Bing Search settings.

    The settings are first loaded from environment variables with the prefix 'BING_'. If the
    environment variables are not found, the settings can be loaded from a .env file with the
    encoding 'utf-8'. If the settings are not found in the .env file, the settings are ignored;
    however, validation will fail alerting that the settings are missing.

    Optional settings for prefix 'BING_' are:
    - api_key: SecretStr - The Bing API key (Env var BING_API_KEY)
    - custom_config: str - The Bing Custom Search instance's unique identifier (Env var BING_CUSTOM_CONFIG)

    """

    env_prefix: ClassVar[str] = "BING_"

    api_key: SecretStr
    custom_config: str | None = None


# endregion BingSettings

# region BingWebPage


@experimental
class BingWebPage(KernelBaseModel):
    """A Bing web page."""

    id: str | None = None
    name: str | None = None
    url: str | None = None
    display_url: str | None = None
    snippet: str | None = None
    date_last_crawled: str | None = None
    deep_links: list["BingWebPage"] | None = None
    open_graph_image: list[dict[str, str | int]] | None = None
    search_tags: list[dict[str, str]] | None = None
    language: str | None = None
    is_family_friendly: bool | None = None
    is_navigational: bool | None = None


@experimental
class BingWebPages(KernelBaseModel):
    """The web pages from a Bing search."""

    id: str | None = None
    some_results_removed: bool | None = Field(default=None, alias="someResultsRemoved")
    total_estimated_matches: int | None = Field(default=None, alias="totalEstimatedMatches")
    web_search_url: str | None = Field(default=None, alias="webSearchUrl")
    value: list[BingWebPage] = Field(default_factory=list)


@experimental
class BingSearchResponse(KernelBaseModel):
    """The response from a Bing search."""

    type_: str = Field(default="", alias="_type")
    query_context: dict[str, Any] = Field(default_factory=dict, validation_alias="queryContext")
    web_pages: BingWebPages | None = Field(default=None, alias="webPages")


# endregion BingWebPage


@experimental
class BingSearch(KernelBaseModel, TextSearch):
    """A search engine connector that uses the Bing Search API to perform a web search."""

    settings: BingSettings

    def __init__(
        self,
        api_key: str | None = None,
        custom_config: str | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
    ) -> None:
        """Initializes a new instance of the Bing Search class.

        Args:
            api_key: The Bing Search API key. If provided, will override
                the value in the env vars or .env file.
            custom_config: The Bing Custom Search instance's unique identifier.
                If provided, will override the value in the env vars or .env file.
            env_file_path: The optional path to the .env file. If provided,
                the settings are read from this file path location.
            env_file_encoding: The optional encoding of the .env file.
        """
        try:
            settings = BingSettings(
                api_key=api_key,
                custom_config=custom_config,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as ex:
            raise ServiceInitializationError("Failed to create Bing settings.") from ex

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
    ) -> "KernelSearchResults[BingWebPage]":
        """Search for text, returning a KernelSearchResult with the results directly from the service."""
        options = self._get_options(options, **kwargs)
        results = await self._inner_search(query=query, options=options)
        return KernelSearchResults(
            results=self._get_bing_web_pages(results),
            total_count=self._get_total_count(results, options),
            metadata=self._get_metadata(results),
        )

    async def _get_result_strings(self, response: BingSearchResponse) -> AsyncIterable[str]:
        if response.web_pages is None:
            return
        for web_page in response.web_pages.value:
            yield web_page.snippet or ""

    async def _get_text_search_results(self, response: BingSearchResponse) -> AsyncIterable[TextSearchResult]:
        if response.web_pages is None:
            return
        for web_page in response.web_pages.value:
            yield TextSearchResult(
                name=web_page.name,
                value=web_page.snippet,
                link=web_page.url,
            )

    async def _get_bing_web_pages(self, response: BingSearchResponse) -> AsyncIterable[BingWebPage]:
        if response.web_pages is None:
            return
        for val in response.web_pages.value:
            yield val

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

    def _get_options(self, options: "SearchOptions | None", **kwargs: Any) -> TextSearchOptions:
        if options is not None and isinstance(options, TextSearchOptions):
            return options
        try:
            return TextSearchOptions(**kwargs)
        except ValidationError:
            return TextSearchOptions()

    async def _inner_search(self, query: str, options: TextSearchOptions) -> BingSearchResponse:
        self._validate_options(options)

        logger.info(
            f"Received request for bing web search with \
                params:\nnum_results: {options.top}\noffset: {options.skip}"
        )

        url = self._get_url()
        params = self._build_request_parameters(query, options)

        logger.info(f"Sending GET request to {url}")

        headers = {
            "Ocp-Apim-Subscription-Key": self.settings.api_key.get_secret_value(),
            "user_agent": SEMANTIC_KERNEL_USER_AGENT,
        }
        try:
            async with AsyncClient(timeout=5) as client:
                response = await client.get(url, headers=headers, params=params)
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

    def _validate_options(self, options: TextSearchOptions) -> None:
        if options.top >= 50:
            raise ServiceInvalidRequestError("count value must be less than 50.")

    def _get_url(self) -> str:
        if not self.settings.custom_config:
            return DEFAULT_URL
        return f"{DEFAULT_CUSTOM_URL}&customConfig={self.settings.custom_config}"

    def _build_request_parameters(self, query: str, options: TextSearchOptions) -> dict[str, str | int]:
        params: dict[str, str | int] = {"count": options.top, "offset": options.skip}
        if not options.filter:
            params["q"] = query or ""
            return params
        extra_query_params = []
        for filter in options.filter.filters:
            if isinstance(filter, SearchFilter):
                logger.warning("Groups are not supported by Bing search, ignored.")
                continue
            if isinstance(filter, EqualTo):
                if filter.field_name in QUERY_PARAMETERS:
                    params[filter.field_name] = escape(filter.value)
                else:
                    extra_query_params.append(f"{filter.field_name}:{filter.value}")
            elif isinstance(filter, AnyTagsEqualTo):
                logger.debug("Any tag equals to filter is not supported by Bing Search API.")
        params["q"] = f"{query}+{f' {options.filter.group_type} '.join(extra_query_params)}".strip()
        return params


__all__ = ["BingSearch", "BingSearchResponse", "BingWebPage"]
