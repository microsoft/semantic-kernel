# Copyright (c) Microsoft. All rights reserved.

import json
import logging
from typing import Annotated, Any

import aiohttp

from semantic_kernel.exceptions import FunctionExecutionException
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.kernel_pydantic import KernelBaseModel

logger = logging.getLogger(__name__)


class WebScraperPlugin(KernelBaseModel):
    """A plugin that provides web scraping functionality using CRW.

    CRW is an open-source web scraper for AI agents that exposes a
    Firecrawl-compatible REST API. It supports scraping single pages,
    crawling entire websites, and discovering site maps.

    GitHub: https://github.com/nicepkg/crw

    Usage:
        kernel.add_plugin(
            WebScraperPlugin(base_url="http://localhost:3000"),
            "WebScraper",
        )

        # With authentication:
        kernel.add_plugin(
            WebScraperPlugin(
                base_url="http://localhost:3000",
                api_key="fc-your-api-key",
            ),
            "WebScraper",
        )

    Examples:
        {{WebScraper.scrape_url "https://example.com"}}
        {{WebScraper.crawl_website "https://example.com"}}
        {{WebScraper.map_site "https://example.com"}}
    """

    base_url: str = "http://localhost:3000"
    """Base URL of the CRW server."""

    api_key: str | None = None
    """Optional Bearer token for authenticating with the CRW server."""

    def _headers(self) -> dict[str, str]:
        """Build request headers including auth if configured."""
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def _post(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        """Send a POST request to the CRW server and return the JSON response."""
        url = f"{self.base_url.rstrip('/')}{path}"
        async with (
            aiohttp.ClientSession() as session,
            session.post(url, headers=self._headers(), data=json.dumps(body)) as response,
        ):
            result = await response.json()
            if response.status >= 400:
                error_msg = result.get("error", f"HTTP {response.status}")
                raise FunctionExecutionException(f"CRW request failed: {error_msg}")
            return result

    async def _get(self, path: str) -> dict[str, Any]:
        """Send a GET request to the CRW server and return the JSON response."""
        url = f"{self.base_url.rstrip('/')}{path}"
        async with (
            aiohttp.ClientSession() as session,
            session.get(url, headers=self._headers()) as response,
        ):
            result = await response.json()
            if response.status >= 400:
                error_msg = result.get("error", f"HTTP {response.status}")
                raise FunctionExecutionException(f"CRW request failed: {error_msg}")
            return result

    @kernel_function(
        name="scrape_url",
        description="Scrape a web page and return its content as markdown",
    )
    async def scrape_url(
        self,
        url: Annotated[str, "The URL to scrape"],
        formats: Annotated[str | None, "Comma-separated output formats (markdown, html, links, plainText)"] = None,
        only_main_content: Annotated[bool, "Strip navigation, footer, and sidebar content"] = True,
        css_selector: Annotated[str | None, "CSS selector to extract specific elements"] = None,
    ) -> str:
        """Scrape a single web page and return its content.

        Args:
            url: The URL to scrape (must be http or https).
            formats: Comma-separated output formats. Defaults to "markdown".
            only_main_content: If True, strips navigation, footer, sidebar.
            css_selector: Optional CSS selector to extract specific elements.

        Returns:
            The scraped content as a string.
        """
        if not url:
            raise FunctionExecutionException("url cannot be `None` or empty")

        body: dict[str, Any] = {
            "url": url,
            "onlyMainContent": only_main_content,
        }

        if formats:
            body["formats"] = [f.strip() for f in formats.split(",")]
        else:
            body["formats"] = ["markdown"]

        if css_selector:
            body["cssSelector"] = css_selector

        result = await self._post("/v1/scrape", body)

        data = result.get("data", {})

        # Return markdown first, then fall back to other formats
        if data.get("markdown"):
            return data["markdown"]
        if data.get("html"):
            return data["html"]
        if data.get("plainText"):
            return data["plainText"]
        if data.get("links"):
            return json.dumps(data["links"])

        return json.dumps(data)

    @kernel_function(
        name="crawl_website",
        description="Crawl a website starting from a URL, following links up to a specified depth",
    )
    async def crawl_website(
        self,
        url: Annotated[str, "The starting URL to crawl"],
        max_depth: Annotated[int, "Maximum link-follow depth"] = 2,
        max_pages: Annotated[int, "Maximum number of pages to scrape"] = 10,
    ) -> str:
        """Start a crawl job and return the crawl job ID.

        The crawl runs asynchronously. Use check_crawl_status to poll for results.

        Args:
            url: The starting URL to crawl.
            max_depth: Maximum link-follow depth (default 2).
            max_pages: Maximum pages to scrape (default 10).

        Returns:
            The crawl job ID that can be used with check_crawl_status.
        """
        if not url:
            raise FunctionExecutionException("url cannot be `None` or empty")

        body: dict[str, Any] = {
            "url": url,
            "maxDepth": max_depth,
            "maxPages": max_pages,
            "formats": ["markdown"],
        }

        result = await self._post("/v1/crawl", body)
        crawl_id = result.get("id", "")
        if not crawl_id:
            raise FunctionExecutionException("CRW did not return a crawl job ID")

        return crawl_id

    @kernel_function(
        name="check_crawl_status",
        description="Check the status and results of a crawl job",
    )
    async def check_crawl_status(
        self,
        crawl_id: Annotated[str, "The crawl job ID returned by crawl_website"],
    ) -> str:
        """Check the status of a running or completed crawl job.

        Args:
            crawl_id: The crawl job ID returned by crawl_website.

        Returns:
            JSON string with crawl status and any available results.
        """
        if not crawl_id:
            raise FunctionExecutionException("crawl_id cannot be `None` or empty")

        result = await self._get(f"/v1/crawl/{crawl_id}")

        status = result.get("status", "unknown")
        pages = result.get("data", [])

        summary: dict[str, Any] = {
            "status": status,
            "total": result.get("total", 0),
            "completed": result.get("completed", 0),
        }

        if pages:
            summary["pages"] = [
                {
                    "url": page.get("metadata", {}).get("sourceURL", ""),
                    "title": page.get("metadata", {}).get("title", ""),
                    "markdown": page.get("markdown", "")[:500],
                }
                for page in pages
            ]

        return json.dumps(summary, indent=2)

    @kernel_function(
        name="map_site",
        description="Discover all URLs on a website by following links and reading sitemaps",
    )
    async def map_site(
        self,
        url: Annotated[str, "The URL to discover links from"],
        max_depth: Annotated[int, "Maximum discovery depth"] = 2,
        use_sitemap: Annotated[bool, "Also read sitemap.xml"] = True,
    ) -> str:
        """Discover all URLs on a website.

        Args:
            url: The URL to discover links from.
            max_depth: Maximum discovery depth (default 2).
            use_sitemap: Whether to also read sitemap.xml (default True).

        Returns:
            JSON array of discovered URLs.
        """
        if not url:
            raise FunctionExecutionException("url cannot be `None` or empty")

        body: dict[str, Any] = {
            "url": url,
            "maxDepth": max_depth,
            "useSitemap": use_sitemap,
        }

        result = await self._post("/v1/map", body)
        links = result.get("data", {}).get("links", [])
        return json.dumps(links)
