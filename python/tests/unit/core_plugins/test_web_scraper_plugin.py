# Copyright (c) Microsoft. All rights reserved.

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from semantic_kernel import Kernel
from semantic_kernel.core_plugins.web_scraper_plugin import WebScraperPlugin
from semantic_kernel.exceptions import FunctionExecutionException


async def test_it_can_be_instantiated():
    plugin = WebScraperPlugin()
    assert plugin is not None
    assert plugin.base_url == "http://localhost:3000"
    assert plugin.api_key is None


async def test_it_can_be_instantiated_with_config():
    plugin = WebScraperPlugin(
        base_url="http://crw.example.com:4000",
        api_key="fc-test-key",
    )
    assert plugin.base_url == "http://crw.example.com:4000"
    assert plugin.api_key == "fc-test-key"


async def test_it_can_be_imported():
    kernel = Kernel()
    plugin = WebScraperPlugin()
    kernel.add_plugin(plugin, "WebScraper")
    assert kernel.get_plugin(plugin_name="WebScraper") is not None
    assert kernel.get_function(plugin_name="WebScraper", function_name="scrape_url") is not None
    assert kernel.get_function(plugin_name="WebScraper", function_name="crawl_website") is not None
    assert kernel.get_function(plugin_name="WebScraper", function_name="check_crawl_status") is not None
    assert kernel.get_function(plugin_name="WebScraper", function_name="map_site") is not None


async def test_headers_without_api_key():
    plugin = WebScraperPlugin()
    headers = plugin._headers()
    assert headers == {"Content-Type": "application/json"}
    assert "Authorization" not in headers


async def test_headers_with_api_key():
    plugin = WebScraperPlugin(api_key="fc-secret")
    headers = plugin._headers()
    assert headers["Authorization"] == "Bearer fc-secret"


def _mock_response(json_data, status=200):
    """Create a mock aiohttp response."""
    mock_resp = AsyncMock()
    mock_resp.status = status
    mock_resp.json = AsyncMock(return_value=json_data)
    return mock_resp


@patch("aiohttp.ClientSession")
async def test_scrape_url(mock_session_cls):
    response_data = {
        "success": True,
        "data": {
            "markdown": "# Example\n\nHello world",
            "metadata": {"title": "Example", "sourceURL": "https://example.com"},
        },
    }
    mock_resp = _mock_response(response_data)
    mock_session = MagicMock()
    mock_session.post = MagicMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_resp)))
    mock_session.close = AsyncMock()
    mock_session_cls.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session_cls.return_value.__aexit__ = AsyncMock(return_value=False)

    plugin = WebScraperPlugin()
    result = await plugin.scrape_url("https://example.com")
    assert result == "# Example\n\nHello world"


async def test_scrape_url_empty_url():
    plugin = WebScraperPlugin()
    with pytest.raises(FunctionExecutionException):
        await plugin.scrape_url("")


async def test_crawl_website_empty_url():
    plugin = WebScraperPlugin()
    with pytest.raises(FunctionExecutionException):
        await plugin.crawl_website("")


async def test_check_crawl_status_empty_id():
    plugin = WebScraperPlugin()
    with pytest.raises(FunctionExecutionException):
        await plugin.check_crawl_status("")


async def test_map_site_empty_url():
    plugin = WebScraperPlugin()
    with pytest.raises(FunctionExecutionException):
        await plugin.map_site("")


@patch("aiohttp.ClientSession")
async def test_crawl_website(mock_session_cls):
    response_data = {"success": True, "id": "abc-123"}
    mock_resp = _mock_response(response_data)
    mock_session = MagicMock()
    mock_session.post = MagicMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_resp)))
    mock_session.close = AsyncMock()
    mock_session_cls.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session_cls.return_value.__aexit__ = AsyncMock(return_value=False)

    plugin = WebScraperPlugin()
    result = await plugin.crawl_website("https://example.com", max_depth=3, max_pages=5)
    assert result == "abc-123"


@patch("aiohttp.ClientSession")
async def test_check_crawl_status(mock_session_cls):
    response_data = {
        "status": "completed",
        "total": 1,
        "completed": 1,
        "data": [
            {
                "markdown": "# Example",
                "metadata": {"title": "Example", "sourceURL": "https://example.com"},
            }
        ],
    }
    mock_resp = _mock_response(response_data)
    mock_session = MagicMock()
    mock_session.get = MagicMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_resp)))
    mock_session.close = AsyncMock()
    mock_session_cls.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session_cls.return_value.__aexit__ = AsyncMock(return_value=False)

    plugin = WebScraperPlugin()
    result = await plugin.check_crawl_status("abc-123")
    parsed = json.loads(result)
    assert parsed["status"] == "completed"
    assert parsed["total"] == 1
    assert len(parsed["pages"]) == 1


@patch("aiohttp.ClientSession")
async def test_map_site(mock_session_cls):
    response_data = {
        "success": True,
        "data": {"links": ["https://example.com", "https://example.com/about"]},
    }
    mock_resp = _mock_response(response_data)
    mock_session = MagicMock()
    mock_session.post = MagicMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_resp)))
    mock_session.close = AsyncMock()
    mock_session_cls.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session_cls.return_value.__aexit__ = AsyncMock(return_value=False)

    plugin = WebScraperPlugin()
    result = await plugin.map_site("https://example.com")
    links = json.loads(result)
    assert len(links) == 2
    assert "https://example.com/about" in links


@patch("aiohttp.ClientSession")
async def test_scrape_url_error_response(mock_session_cls):
    response_data = {"success": False, "error": "invalid_url"}
    mock_resp = _mock_response(response_data, status=400)
    mock_session = MagicMock()
    mock_session.post = MagicMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_resp)))
    mock_session.close = AsyncMock()
    mock_session_cls.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session_cls.return_value.__aexit__ = AsyncMock(return_value=False)

    plugin = WebScraperPlugin()
    with pytest.raises(FunctionExecutionException, match="CRW request failed"):
        await plugin.scrape_url("not-a-url")


@patch("aiohttp.ClientSession")
async def test_scrape_url_with_formats(mock_session_cls):
    response_data = {
        "success": True,
        "data": {
            "markdown": "# Example",
            "links": ["https://example.com/a"],
        },
    }
    mock_resp = _mock_response(response_data)
    mock_session = MagicMock()
    mock_session.post = MagicMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_resp)))
    mock_session.close = AsyncMock()
    mock_session_cls.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session_cls.return_value.__aexit__ = AsyncMock(return_value=False)

    plugin = WebScraperPlugin()
    result = await plugin.scrape_url("https://example.com", formats="markdown, links")
    assert result == "# Example"
