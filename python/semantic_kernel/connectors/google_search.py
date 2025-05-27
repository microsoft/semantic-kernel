# Copyright (c) Microsoft. All rights reserved.

import ast
import logging
import sys
from collections.abc import AsyncIterable, Callable
from inspect import getsource
from typing import Any, ClassVar, Final, Literal
from urllib.parse import quote_plus

from httpx import AsyncClient, HTTPStatusError, RequestError
from pydantic import Field, SecretStr, ValidationError

from semantic_kernel.connectors._search_shared import SearchLambdaVisitor
from semantic_kernel.data.text_search import (
    KernelSearchResults,
    SearchOptions,
    TextSearch,
    TextSearchResult,
    TSearchResult,
)
from semantic_kernel.exceptions import ServiceInitializationError, ServiceInvalidRequestError
from semantic_kernel.kernel_pydantic import KernelBaseModel, KernelBaseSettings
from semantic_kernel.kernel_types import OptionalOneOrList
from semantic_kernel.utils.feature_stage_decorator import experimental
from semantic_kernel.utils.telemetry.user_agent import SEMANTIC_KERNEL_USER_AGENT

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override

logger: logging.Logger = logging.getLogger(__name__)

CUSTOM_SEARCH_URL: Final[str] = "https://www.googleapis.com/customsearch/v1"
# For more info on this list: https://developers.google.com/custom-search/v1/reference/rest/v1/cse/list
QUERY_PARAMETERS: Final[list[str]] = [
    # Country, Restricts search results to documents originating in a particular country.
    # You may use Boolean operators in the cr parameter's value.
    "cr",
    # Date Restrict, Restricts results to URLs based on date. Supported values include:
    # d[number]: requests results from the specified number of past days.
    # w[number]: requests results from the specified number of past weeks.
    # m[number]: requests results from the specified number of past months.
    # y[number]: requests results from the specified number of past years.
    "dateRestrict",
    # exactTerms, Identifies a phrase that all documents in the search results must contain.
    "exactTerms",
    # excludeTerms, Identifies a word or phrase that should not appear in any documents in the search results.
    "excludeTerms",
    # fileType, Restricts results to files of a specified extension. A list of file types indexable by Google
    # can be found in Search Console Help Center: https://support.google.com/webmasters/answer/35287
    "fileType",
    # filter, Controls turning on or off the duplicate content filter.
    "filter",
    # gl, Geolocation of end user. The gl parameter value is a two-letter country code. The gl parameter boosts search
    # results whose country of origin matches the parameter value.
    # See the Country Codes page for a list of valid values.
    "gl",
    # highRange, Specifies the ending value for a search range.
    "highRange",
    # hl, Sets the user interface language.
    "hl",
    # linkSite, Specifies that all search results should contain a link to a particular URL.
    "linkSite",
    # Language of the result. Restricts the search to documents written in a particular language (e.g., lr=lang_ja).
    "lr",
    # or Terms, Provides additional search terms to check for in a document, where each document in the search results
    # must contain at least one of the additional search terms.
    "orTerms",
    # rights, Filters based on licensing. Supported values include:
    # cc_publicdomain, cc_attribute, cc_sharealike, cc_noncommercial, cc_nonderived
    "rights",
    # siteSearch, Specifies all search results should be pages from a given site.
    "siteSearch",
    # siteSearchFilter, Controls whether to include or exclude results from the site named in the siteSearch parameter.
    "siteSearchFilter",
]


@experimental
class GoogleSearchResult(KernelBaseModel):
    """A Google web page."""

    kind: str = ""
    title: str = ""
    html_title: str = Field(default="", alias="htmlTitle")
    link: str = ""
    display_link: str = Field(default="", alias="displayLink")
    snippet: str = ""
    html_snippet: str = Field(default="", alias="htmlSnippet")
    cache_id: str = Field(default="", alias="cacheId")
    formatted_url: str = Field(default="", alias="formattedUrl")
    html_formatted_url: str = Field(default="", alias="htmlFormattedUrl")
    pagemap: dict[str, Any] = Field(default_factory=dict)
    mime: str = ""
    file_format: str = Field(default="", alias="fileFormat")
    image: dict[str, Any] = Field(default_factory=dict)
    labels: list[dict[str, Any]] = Field(default_factory=list)


@experimental
class GoogleSearchInformation(KernelBaseModel):
    """Information about the search."""

    search_time: float = Field(alias="searchTime")
    formatted_search_time: str = Field(alias="formattedSearchTime")
    total_results: str = Field(alias="totalResults")
    formatted_total_results: str = Field(alias="formattedTotalResults")


@experimental
class GoogleSearchResponse(KernelBaseModel):
    """The response from a Google search."""

    kind: str = ""
    url: dict[str, str] = Field(default_factory=dict)
    queries: dict[str, list[dict[str, str | int]]] = Field(default_factory=dict)
    context: dict[str, Any] = Field(default_factory=dict)
    search_information: GoogleSearchInformation | None = None
    spelling: dict[str, Any] = Field(default_factory=dict)
    promotions: list[dict[str, Any]] = Field(default_factory=list)
    items: list[GoogleSearchResult] | None = Field(None)


class GoogleSearchSettings(KernelBaseSettings):
    """Google Search Connector settings.

    The settings are first loaded from environment variables with the prefix 'GOOGLE_'. If the
    environment variables are not found, the settings can be loaded from a .env file with the
    encoding 'utf-8'. If the settings are not found in the .env file, the settings are ignored;
    however, validation will fail alerting that the settings are missing.

    Required settings for prefix 'GOOGLE_SEARCH_' are:
    - api_key: SecretStr - The Google Search API key (Env var GOOGLE_SEARCH_API_KEY)

    Optional settings for prefix 'GOOGLE_SEARCH_' are:
    - engine_id: str - The Google search engine ID (Env var GOOGLE_SEARCH_ENGINE_ID)
    - env_file_path: str | None - if provided, the .env settings are read from this file path location
    - env_file_encoding: str - if provided, the .env file encoding used. Defaults to "utf-8".
    """

    env_prefix: ClassVar[str] = "GOOGLE_SEARCH_"

    api_key: SecretStr
    engine_id: str | None = None


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

    @override
    async def search(
        self,
        query: str,
        output_type: type[str] | type[TSearchResult] | Literal["Any"] = str,
        *,
        filter: OptionalOneOrList[Callable | str] = None,
        skip: int = 0,
        top: int = 5,
        include_total_count: bool = False,
        **kwargs: Any,
    ) -> "KernelSearchResults[TSearchResult]":
        options = SearchOptions(filter=filter, skip=skip, top=top, include_total_count=include_total_count, **kwargs)
        results = await self._inner_search(query=query, options=options)
        return KernelSearchResults(
            results=self._get_result_strings(results)
            if output_type is str
            else self._get_text_search_results(results)
            if output_type is TextSearchResult
            else self._get_google_search_results(results),
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

    def _get_total_count(self, response: GoogleSearchResponse, options: SearchOptions) -> int | None:
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

    def _get_options(self, options: "SearchOptions | None", **kwargs: Any) -> SearchOptions:
        if options is not None and isinstance(options, SearchOptions):
            return options
        try:
            return SearchOptions(**kwargs)
        except ValidationError:
            return SearchOptions()

    async def _inner_search(self, query: str, options: SearchOptions) -> GoogleSearchResponse:
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

    def _validate_options(self, options: SearchOptions) -> None:
        if options.top > 10:
            raise ServiceInvalidRequestError("count value must be less than or equal to 10.")

    def _parse_filter_lambda(self, filter_lambda: Callable | str) -> list[dict[str, str]]:
        """Parse a string lambda or string expression into a list of {field: value} dicts using AST."""
        expr = filter_lambda if isinstance(filter_lambda, str) else getsource(filter_lambda).strip()
        tree = ast.parse(expr, mode="eval")
        node = tree.body
        visitor = SearchLambdaVisitor(valid_parameters=QUERY_PARAMETERS)
        visitor.visit(node)
        return visitor.filters

    def _build_query(self, query: str, options: SearchOptions) -> str:
        params = {
            "key": self.settings.api_key.get_secret_value(),
            "cx": self.settings.engine_id,
            "num": options.top,
            "start": options.skip,
        }
        # parse the filter lambdas to query parameters
        if options.filter:
            filters = options.filter
            if not isinstance(filters, list):
                filters = [filters]
            for f in filters:
                try:
                    for d in self._parse_filter_lambda(f):
                        params.update(d)
                except Exception as exc:
                    logger.warning(f"Failed to parse filter lambda: {f}, ignoring this filter. Error: {exc}")
                    continue
        return f"?q={quote_plus(query)}&{'&'.join(f'{k}={v}' for k, v in params.items())}"
