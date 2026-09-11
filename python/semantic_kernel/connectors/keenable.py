# Copyright (c) Microsoft. All rights reserved.

import ast
import logging
import sys
from collections.abc import AsyncIterable, Callable
from inspect import getsource
from typing import Any, ClassVar, Final, Literal
from urllib.parse import unquote_plus

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

# region Constants
DEFAULT_URL: Final[str] = "https://api.keenable.ai/v1/search"
DEFAULT_PUBLIC_URL: Final[str] = "https://api.keenable.ai/v1/search/public"
APP_TITLE: Final[str] = "semantic-kernel"
MAX_RESULTS: Final[int] = 50
QUERY_PARAMETERS: Final[list[str]] = [
    "site",
    "published_after",
    "published_before",
]


# endregion Constants


# region KeenableSettings
class KeenableSettings(KernelBaseSettings):
    """Keenable Connector settings.

    The settings are first loaded from environment variables with the prefix 'KEENABLE_'. If the
    environment variables are not found, the settings can be loaded from a .env file with the
    encoding 'utf-8'. All settings are optional: without an API key the connector calls the public
    endpoint, which is rate limited per IP.

    Optional settings for prefix 'KEENABLE_' are:
    - api_key: SecretStr - The Keenable API key (Env var KEENABLE_API_KEY). Lifts the rate limits.

    """

    env_prefix: ClassVar[str] = "KEENABLE_"

    api_key: SecretStr | None = None


# endregion KeenableSettings


# region KeenableWeb
@experimental
class KeenableWebPage(KernelBaseModel):
    """A Keenable search result."""

    title: str | None = None
    url: str | None = None
    snippet: str | None = None
    description: str | None = None
    published_at: str | None = None
    acquired_at: str | None = None

    @property
    def text(self) -> str:
        """The page text: the snippet, falling back to the description."""
        return self.snippet or self.description or ""


@experimental
class KeenableSearchResponse(KernelBaseModel):
    """The response from a Keenable search."""

    query: str | None = None
    results: list[KeenableWebPage] = Field(default_factory=list)


# endregion KeenableWeb


@experimental
class KeenableSearch(KernelBaseModel, TextSearch):
    """A search engine connector that uses the Keenable Search API to perform a web search.

    The connector works without an API key: it then calls the public endpoint, which is
    rate limited per IP. Setting KEENABLE_API_KEY switches to the authenticated endpoint
    and lifts those limits.
    """

    settings: KeenableSettings

    def __init__(
        self,
        api_key: str | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
    ) -> None:
        """Initializes a new instance of the Keenable Search class.

        Args:
            api_key: The Keenable API key. Optional; if provided, will override
                the value in the env vars or .env file. Without a key the public
                endpoint is used.
            env_file_path: The optional path to the .env file. If provided,
                the settings are read from this file path location.
            env_file_encoding: The optional encoding of the .env file. If provided,
                the settings are read from this file path location.
        """
        try:
            settings = KeenableSettings(
                api_key=api_key,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as ex:
            raise ServiceInitializationError("Failed to create Keenable settings.") from ex

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
            else self._get_keenable_web_pages(results),
            total_count=self._get_total_count(results, options),
            metadata=self._get_metadata(results),
        )

    async def _get_result_strings(self, response: KeenableSearchResponse) -> AsyncIterable[str]:
        for web_page in response.results:
            yield web_page.text

    async def _get_text_search_results(self, response: KeenableSearchResponse) -> AsyncIterable[TextSearchResult]:
        for web_page in response.results:
            yield TextSearchResult(
                name=web_page.title,
                value=web_page.text,
                link=web_page.url,
            )

    async def _get_keenable_web_pages(self, response: KeenableSearchResponse) -> AsyncIterable[KeenableWebPage]:
        for val in response.results:
            yield val

    def _get_metadata(self, response: KeenableSearchResponse) -> dict[str, Any]:
        return {"query": response.query}

    def _get_total_count(self, response: KeenableSearchResponse, options: SearchOptions) -> int | None:
        if options.include_total_count:
            return len(response.results)
        return None

    def _get_options(self, **kwargs: Any) -> SearchOptions:
        try:
            return SearchOptions(**kwargs)
        except ValidationError:
            return SearchOptions()

    async def _inner_search(self, query: str, options: SearchOptions) -> KeenableSearchResponse:
        self._validate_options(options)

        logger.info(
            f"Received request for keenable web search with \
                params:\nnum_results: {options.top}\noffset: {options.skip}"
        )

        url = self._get_url()
        headers = self._get_headers()
        body = self._build_request_body(query, options)

        logger.info(f"Sending POST request to {url}")

        try:
            async with AsyncClient(timeout=10) as client:
                response = await client.post(url, headers=headers, json=body)
                response.raise_for_status()
                parsed = KeenableSearchResponse.model_validate_json(response.text)
        except HTTPStatusError as ex:
            logger.error(f"Failed to get search results: {ex}")
            if ex.response.status_code == 429:
                hint = "" if self._get_api_key() else " Set KEENABLE_API_KEY to lift the limits of the public endpoint."
                raise ServiceInvalidRequestError(f"Keenable rate limit reached.{hint}") from ex
            raise ServiceInvalidRequestError("Failed to get search results.") from ex
        except RequestError as ex:
            logger.error(f"Client error occurred: {ex}")
            raise ServiceInvalidRequestError("A client error occurred while getting search results.") from ex
        except Exception as ex:
            logger.error(f"An unexpected error occurred: {ex}")
            raise ServiceInvalidRequestError("An unexpected error occurred while getting search results.") from ex

        # The API has no offset parameter, so `skip` is applied here: the request asks
        # for `top + skip` results and the first `skip` are dropped.
        if options.skip:
            parsed.results = parsed.results[options.skip :]
        return parsed

    def _validate_options(self, options: SearchOptions) -> None:
        if options.top <= 0:
            raise ServiceInvalidRequestError("top value must be greater than 0.")
        if options.skip < 0:
            raise ServiceInvalidRequestError("skip must be greater than or equal to 0.")
        if options.top + options.skip > MAX_RESULTS:
            raise ServiceInvalidRequestError(f"top plus skip must not exceed {MAX_RESULTS}.")

    def _get_api_key(self) -> str | None:
        if self.settings.api_key is None:
            return None
        return self.settings.api_key.get_secret_value() or None

    def _get_url(self) -> str:
        return DEFAULT_URL if self._get_api_key() else DEFAULT_PUBLIC_URL

    def _get_headers(self) -> dict[str, str]:
        # X-Keenable-Title identifies the calling application; the public endpoint requires it.
        headers = {"X-Keenable-Title": APP_TITLE, "User-Agent": SEMANTIC_KERNEL_USER_AGENT}
        api_key = self._get_api_key()
        if api_key:
            headers["X-API-Key"] = api_key
        return headers

    def _parse_filter_lambda(self, filter_lambda: Callable | str) -> list[dict[str, str]]:
        """Parse a string lambda or string expression into a list of {field: value} dicts using AST."""
        expr = filter_lambda if isinstance(filter_lambda, str) else getsource(filter_lambda).strip()
        tree = ast.parse(expr, mode="eval")
        node = tree.body
        visitor = SearchLambdaVisitor(valid_parameters=QUERY_PARAMETERS)
        visitor.visit(node)
        return visitor.filters

    def _build_request_body(self, query: str, options: SearchOptions) -> dict[str, str | int]:
        body: dict[str, str | int] = {
            "query": query or "",
            "max_results": options.top + options.skip,
        }
        if not options.filter:
            return body
        filters = options.filter
        if not isinstance(filters, list):
            filters = [filters]
        for f in filters:
            try:
                for d in self._parse_filter_lambda(f):
                    for field, value in d.items():
                        # SearchLambdaVisitor URL-encodes values for query strings;
                        # this API takes a JSON body, so decode them again.
                        body[field] = unquote_plus(value)
            except Exception as exc:
                logger.warning(f"Failed to parse filter lambda: {f}, ignoring this filter. Error: {exc}")
                continue
        return body
