# Copyright (c) Microsoft. All rights reserved.

import ast
import logging
import sys
from collections.abc import AsyncIterable, Callable
from inspect import getsource
from typing import Any, ClassVar, Final, Literal

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
DEFAULT_URL: Final[str] = "https://api.serpex.dev/api/search"
SUPPORTED_ENGINES: Final[list[str]] = ["auto", "google", "bing", "duckduckgo", "brave", "yahoo", "yandex"]
QUERY_PARAMETERS: Final[list[str]] = [
    "engine",
    "category",
    "time_range",
]
# endregion Constants


# region SerpexSettings
class SerpexSettings(KernelBaseSettings):
    """Serpex Connector settings.

    The settings are first loaded from environment variables with the prefix 'SERPEX_'. If the
    environment variables are not found, the settings can be loaded from a .env file with the
    encoding 'utf-8'. If the settings are not found in the .env file, the settings are ignored;
    however, validation will fail alerting that the settings are missing.

    Required settings for prefix 'SERPEX_' are:
    - api_key: SecretStr - The Serpex API key (Env var SERPEX_API_KEY)
    
    Optional settings for prefix 'SERPEX_' are:
    - engine: str - Search engine to use (default: "auto", options: auto, google, bing, duckduckgo, brave, yahoo, yandex)
    - category: str - Search category (default: "web")
    - time_range: str | None - Time range filter (options: all, day, week, month, year)
    """

    env_prefix: ClassVar[str] = "SERPEX_"

    api_key: SecretStr
    engine: str = "auto"
    category: str = "web"
    time_range: str | None = None


# endregion SerpexSettings


# region SerpexResult
@experimental
class SerpexResult(KernelBaseModel):
    """A Serpex search result."""

    position: int | None = None
    title: str = ""
    url: str = ""
    snippet: str = ""
    published_date: str | None = None
    source: str | None = None


@experimental
class SerpexAnswer(KernelBaseModel):
    """A Serpex instant answer."""

    answer: str = ""
    source: str | None = None


@experimental
class SerpexInfobox(KernelBaseModel):
    """A Serpex knowledge panel/infobox."""

    title: str | None = None
    description: str | None = None
    url: str | None = None
    image: str | None = None


@experimental
class SerpexMetadata(KernelBaseModel):
    """Metadata about the search."""

    number_of_results: int = 0
    request_time: float = 0.0
    engine: str = ""


@experimental
class SerpexResponse(KernelBaseModel):
    """The response from a Serpex search."""

    metadata: SerpexMetadata | None = None
    results: list[SerpexResult] = Field(default_factory=list)
    answers: list[SerpexAnswer] = Field(default_factory=list)
    infoboxes: list[SerpexInfobox] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    corrections: list[str] = Field(default_factory=list)


# endregion SerpexResult


# region SerpexSearch
@experimental
class SerpexSearch(KernelBaseModel, TextSearch):
    """Serpex search connector for multi-engine web search.
    
    Serpex provides unified access to multiple search engines including Google, Bing,
    DuckDuckGo, Brave, Yahoo, and Yandex with intelligent auto-routing and retry logic.
    
    Args:
        api_key: The Serpex API key
        base_url: Optional custom API endpoint (default: https://api.serpex.dev/api/search)
        engine: Search engine to use (default: "auto")
        category: Search category (default: "web")
        time_range: Optional time range filter
        
    Example:
        ```python
        from semantic_kernel.connectors import SerpexSearch
        from pydantic import SecretStr
        
        # Initialize with API key
        search = SerpexSearch(
            api_key=SecretStr("your-api-key"),
            engine="auto"
        )
        
        # Or use environment variables
        search = SerpexSearch()  # Reads SERPEX_API_KEY from env
        
        # Perform search
        results = await search.search("Python programming")
        ```
    """

    api_key: SecretStr
    base_url: str = DEFAULT_URL
    engine: str = "auto"
    category: str = "web"
    time_range: str | None = None

    def __init__(
        self,
        api_key: SecretStr | None = None,
        base_url: str = DEFAULT_URL,
        engine: str = "auto",
        category: str = "web",
        time_range: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the Serpex search connector.
        
        Args:
            api_key: The Serpex API key. If not provided, will try to load from SERPEX_API_KEY env var
            base_url: Custom API endpoint (default: https://api.serpex.dev/api/search)
            engine: Search engine (default: "auto", options: auto, google, bing, duckduckgo, brave, yahoo, yandex)
            category: Search category (default: "web")
            time_range: Time range filter (options: all, day, week, month, year)
            **kwargs: Additional keyword arguments
        """
        if api_key is None:
            try:
                settings = SerpexSettings()
                api_key = settings.api_key
                if not engine or engine == "auto":
                    engine = settings.engine
                if not category:
                    category = settings.category
                if time_range is None:
                    time_range = settings.time_range
            except ValidationError as e:
                raise ServiceInitializationError(
                    "Serpex API key is required. Please provide it via api_key parameter "
                    "or set the SERPEX_API_KEY environment variable."
                ) from e

        if engine not in SUPPORTED_ENGINES:
            raise ServiceInitializationError(
                f"Invalid engine '{engine}'. Supported engines: {', '.join(SUPPORTED_ENGINES)}"
            )

        super().__init__(
            api_key=api_key,
            base_url=base_url,
            engine=engine,
            category=category,
            time_range=time_range,
            **kwargs,
        )

    @override
    async def search(
        self,
        query: str,
        top: int = 10,
        skip: int = 0,
        filter: Callable[[TSearchResult], bool] | None = None,
        options: SearchOptions | None = None,
        **kwargs: Any,
    ) -> KernelSearchResults[TextSearchResult]:
        """Execute a search query using Serpex.
        
        Args:
            query: The search query string
            top: Maximum number of results to return (default: 10)
            skip: Number of results to skip (default: 0)
            filter: Optional filter function
            options: Additional search options
            **kwargs: Additional parameters (engine, category, time_range, etc.)
            
        Returns:
            KernelSearchResults containing TextSearchResult items
        """
        return await self._inner_search(
            query=query, top=top, skip=skip, filter=filter, options=options, **kwargs
        )

    @override
    async def get_text_search_results(
        self,
        query: str,
        top: int = 10,
        skip: int = 0,
        filter: Callable[[TSearchResult], bool] | None = None,
        options: SearchOptions | None = None,
        **kwargs: Any,
    ) -> AsyncIterable[TextSearchResult]:
        """Get async iterable of search results.
        
        Args:
            query: The search query string
            top: Maximum number of results to return
            skip: Number of results to skip
            filter: Optional filter function
            options: Additional search options
            **kwargs: Additional parameters
            
        Yields:
            TextSearchResult items
        """
        results = await self._inner_search(
            query=query, top=top, skip=skip, filter=filter, options=options, **kwargs
        )
        for result in results.results:
            yield result

    @override
    async def get_search_results(
        self,
        query: str,
        top: int = 10,
        skip: int = 0,
        filter: Callable[[TSearchResult], bool] | None = None,
        options: SearchOptions | None = None,
        **kwargs: Any,
    ) -> AsyncIterable[SerpexResult]:
        """Get async iterable of SerpexResult objects.
        
        Args:
            query: The search query string
            top: Maximum number of results to return
            skip: Number of results to skip
            filter: Optional filter function
            options: Additional search options
            **kwargs: Additional parameters
            
        Yields:
            SerpexResult items
        """
        response = await self._execute_search(query=query, **kwargs)
        
        # Apply skip and top
        results = response.results[skip : skip + top]
        
        # Apply filter if provided
        if filter:
            for result in results:
                if filter(result):
                    yield result
        else:
            for result in results:
                yield result

    async def _inner_search(
        self,
        query: str,
        top: int = 10,
        skip: int = 0,
        filter: Callable[[TSearchResult], bool] | None = None,
        options: SearchOptions | None = None,
        **kwargs: Any,
    ) -> KernelSearchResults[TextSearchResult]:
        """Internal search method.
        
        Args:
            query: The search query
            top: Number of results
            skip: Number to skip
            filter: Filter function
            options: Search options
            **kwargs: Additional parameters
            
        Returns:
            KernelSearchResults
        """
        response = await self._execute_search(query=query, **kwargs)
        
        # Convert SerpexResults to TextSearchResults
        text_results: list[TextSearchResult] = []
        for result in response.results[skip : skip + top]:
            text_result = TextSearchResult(
                name=result.title,
                value=result.snippet,
                link=result.url,
            )
            if filter is None or filter(text_result):
                text_results.append(text_result)
        
        return KernelSearchResults(
            results=text_results,
            total_count=len(response.results) if response.metadata else 0,
        )

    async def _execute_search(self, query: str, **kwargs: Any) -> SerpexResponse:
        """Execute the actual API call to Serpex.
        
        Args:
            query: The search query
            **kwargs: Additional parameters (engine, category, time_range)
            
        Returns:
            SerpexResponse object
        """
        params: dict[str, Any] = {
            "q": query,
            "engine": kwargs.get("engine", self.engine),
            "category": kwargs.get("category", self.category),
        }
        
        # Add time_range if specified
        time_range = kwargs.get("time_range", self.time_range)
        if time_range:
            params["time_range"] = time_range
        
        headers = {
            "Authorization": f"Bearer {self.api_key.get_secret_value()}",
            "User-Agent": SEMANTIC_KERNEL_USER_AGENT,
            "Content-Type": "application/json",
        }
        
        async with AsyncClient() as client:
            try:
                logger.debug(f"Executing Serpex search with query: {query}")
                response = await client.get(self.base_url, params=params, headers=headers, timeout=30.0)
                response.raise_for_status()
                
                data = response.json()
                return SerpexResponse(**data)
                
            except HTTPStatusError as e:
                logger.error(f"HTTP error during Serpex search: {e}")
                raise ServiceInvalidRequestError(f"Serpex API request failed: {e}") from e
            except RequestError as e:
                logger.error(f"Request error during Serpex search: {e}")
                raise ServiceInvalidRequestError(f"Failed to connect to Serpex API: {e}") from e
            except Exception as e:
                logger.error(f"Unexpected error during Serpex search: {e}")
                raise ServiceInvalidRequestError(f"Serpex search failed: {e}") from e


# endregion SerpexSearch
