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
DEFAULT_URL: Final[str] = "https://api.exa.ai/search"
QUERY_PARAMETERS: Final[list[str]] = [
    "type",
    "category",
    "userLocation",
    "includeDomains",
    "excludeDomains",
    "includeText",
    "excludeText",
]
LIST_PARAMETERS: Final[list[str]] = [
    "includeDomains",
    "excludeDomains",
    "includeText",
    "excludeText",
]
MAX_TOP: Final[int] = 100


# endregion Constants


# region ExaSettings
class ExaSettings(KernelBaseSettings):
    """Exa Connector settings.

    The settings are first loaded from environment variables with the prefix 'EXA_'. If the
    environment variables are not found, the settings can be loaded from a .env file with the
    encoding 'utf-8'. If the settings are not found in the .env file, the settings are ignored;
    however, validation will fail alerting that the settings are missing.

    Required settings for prefix 'EXA_' are:
    - api_key: SecretStr - The Exa API key (Env var EXA_API_KEY)

    """

    env_prefix: ClassVar[str] = "EXA_"

    api_key: SecretStr


# endregion ExaSettings


# region ExaResults
@experimental
class ExaSearchResult(KernelBaseModel):
    """A single result from an Exa search."""

    id: str | None = None
    title: str | None = None
    url: str | None = None
    text: str | None = None
    highlights: list[str] | None = None
    summary: str | None = None
    author: str | None = None
    published_date: str | None = Field(default=None, validation_alias="publishedDate")
    score: float | None = None
    image: str | None = None
    favicon: str | None = None


@experimental
class ExaSearchResponse(KernelBaseModel):
    """The response from an Exa search."""

    request_id: str | None = Field(default=None, validation_alias="requestId")
    results: list[ExaSearchResult] = Field(default_factory=list)
    search_time: float | None = Field(default=None, validation_alias="searchTime")
    cost_dollars: dict[str, Any] | None = Field(default=None, validation_alias="costDollars")


# endregion ExaResults


@experimental
class ExaSearch(KernelBaseModel, TextSearch):
    """A search engine connector that uses the Exa Search API to perform a web search."""

    settings: ExaSettings

    def __init__(
        self,
        api_key: str | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
    ) -> None:
        """Initializes a new instance of the Exa Search class.

        Args:
            api_key: The Exa Search API key. If provided, will override
                the value in the env vars or .env file.
            env_file_path: The optional path to the .env file. If provided,
                the settings are read from this file path location.
            env_file_encoding: The optional encoding of the .env file. If provided,
                the settings are read from this file path location.
        """
        try:
            settings = ExaSettings(
                api_key=api_key,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as ex:
            raise ServiceInitializationError("Failed to create Exa settings.") from ex

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
            else self._get_exa_results(results),
            total_count=self._get_total_count(results, options),
            metadata=self._get_metadata(results),
        )

    async def _get_result_strings(self, response: ExaSearchResponse) -> AsyncIterable[str]:
        for result in response.results:
            yield self._get_content(result)

    async def _get_text_search_results(self, response: ExaSearchResponse) -> AsyncIterable[TextSearchResult]:
        for result in response.results:
            yield TextSearchResult(
                name=result.title,
                value=self._get_content(result),
                link=result.url,
            )

    async def _get_exa_results(self, response: ExaSearchResponse) -> AsyncIterable[ExaSearchResult]:
        for result in response.results:
            yield result

    @staticmethod
    def _get_content(result: ExaSearchResult) -> str:
        if result.highlights:
            return " ".join(result.highlights)
        return result.summary or result.text or ""

    def _get_metadata(self, response: ExaSearchResponse) -> dict[str, Any]:
        return {
            "request_id": response.request_id,
            "search_time": response.search_time,
            "cost_dollars": response.cost_dollars,
        }

    def _get_total_count(self, response: ExaSearchResponse, options: SearchOptions) -> int | None:
        if options.include_total_count:
            return len(response.results)
        return None

    def _get_options(self, **kwargs: Any) -> SearchOptions:
        try:
            return SearchOptions(**kwargs)
        except ValidationError:
            return SearchOptions()

    async def _inner_search(self, query: str, options: SearchOptions) -> ExaSearchResponse:
        self._validate_options(options)

        logger.info(f"Received request for exa web search with params:\nnum_results: {options.top}")

        url = self._get_url()
        payload = self._build_request_payload(query, options)

        logger.info(f"Sending POST request to {url}")

        headers = {
            "x-api-key": self.settings.api_key.get_secret_value(),
            "Content-Type": "application/json",
            "user_agent": SEMANTIC_KERNEL_USER_AGENT,
            "x-exa-integration": "microsoft/semantic-kernel-integration",
        }
        try:
            async with AsyncClient(timeout=30) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                return ExaSearchResponse.model_validate_json(response.text)
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
        if options.top > MAX_TOP:
            raise ServiceInvalidRequestError(f"numResults value must be less than or equal to {MAX_TOP}.")
        if options.skip:
            raise ServiceInvalidRequestError("Exa search does not support skip/offset pagination.")

    def _get_url(self) -> str:
        return DEFAULT_URL

    def _parse_filter_lambda(self, filter_lambda: Callable | str) -> list[dict[str, str]]:
        """Parse a string lambda or string expression into a list of {field: value} dicts using AST."""
        expr = filter_lambda if isinstance(filter_lambda, str) else getsource(filter_lambda).strip()
        tree = ast.parse(expr, mode="eval")
        node = tree.body
        visitor = SearchLambdaVisitor(valid_parameters=QUERY_PARAMETERS)
        visitor.visit(node)
        return visitor.filters

    def _build_request_payload(self, query: str, options: SearchOptions) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "query": query or "",
            "type": "auto",
            "numResults": options.top,
            "contents": {"highlights": True},
        }
        if not options.filter:
            return payload
        filters = options.filter
        if not isinstance(filters, list):
            filters = [filters]
        for f in filters:
            try:
                for d in self._parse_filter_lambda(f):
                    for field, value in d.items():
                        decoded = unquote_plus(value)
                        if field in LIST_PARAMETERS:
                            payload.setdefault(field, []).append(decoded)
                        else:
                            payload[field] = decoded
            except Exception as exc:
                logger.warning(f"Failed to parse filter lambda: {f}, ignoring this filter. Error: {exc}")
                continue
        return payload
